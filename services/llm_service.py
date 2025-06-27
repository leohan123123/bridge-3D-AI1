# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import httpx # For making HTTP requests to LLM APIs
from config import LLM_CONFIG # Import configurations. config.py now handles .env loading and os.getenv
import json
# import subprocess # For local Ollama CLI calls if needed (alternative to HTTP) - currently unused
from typing import Dict, Any, Optional, Tuple
import asyncio # For sleep
import logging
import time # For performance counter
import os # For os.getenv, though config.py handles it now, direct use in __init__ can be an option

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers: # Ensure logger is not configured multiple times
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LLMService:
    def __init__(self, max_retries=2, retry_delay=1):
        logger.info(f"Initializing LLMService with max_retries={max_retries}, retry_delay={retry_delay}s")
        # LLM_CONFIG from config.py already prioritizes environment variables
        self.deepseek_config = LLM_CONFIG.get("deepseek", {})
        self.ollama_config = LLM_CONFIG.get("ollama", {})
        self.qwen_config = LLM_CONFIG.get("qwen", {}) # Qwen is currently mocked

        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.call_stats = { # For LLM call counts and success rates
            "deepseek": {"attempts": 0, "success": 0, "total_time_s": 0.0, "errors": 0},
            "ollama": {"attempts": 0, "success": 0, "total_time_s": 0.0, "errors": 0},
            "qwen": {"attempts": 0, "success": 0, "total_time_s": 0.0, "errors": 0}
        }
        self.prompt_templates = {
            "extract_bridge_parameters": """
            Analyze the following user requirements for a bridge design and extract key parameters.
            User Requirements: "{user_input}"

            Return the parameters in a JSON format with the following keys (if found, otherwise use null):
            - bridge_type_preference (e.g., "beam", "arch", "suspension", "cable-stayed")
            - span_length_description (e.g., "long river crossing", "short pedestrian bridge", "approx 100m")
            - load_requirements (e.g., "heavy vehicles", "pedestrian only", "railway")
            - site_terrain (e.g., "flat", "mountainous", "urban", "over water")
            - specific_materials (e.g., "steel", "concrete")
            - budget_constraints (e.g., "low budget", "no limit")
            - aesthetic_preferences (e.g., "modern look", "classic design")
            - environmental_factors (e.g., "high winds", "earthquake zone intensity 8", "corrosive environment")
            - road_lanes_description (e.g., "双向四车道", "two lanes with pedestrian walkway", "single track railway")

            Example of desired JSON output:
            {{
                "bridge_type_preference": "cable-stayed bridge with composite deck",
                "span_length_description": "main span approx 500m, side spans 2x200m",
                "load_requirements": "heavy vehicles (highway class A) and future light rail",
                "site_terrain": "over water, coastal area with soft soil",
                "specific_materials": "corrosion-resistant steel for cables and superstructure, high-strength concrete for towers",
                "budget_constraints": "medium to high, focus on durability",
                "aesthetic_preferences": "iconic and modern, slender profile",
                "environmental_factors": "high winds (typhoon prone), saltwater environment, seismic zone intensity 7",
                "road_lanes_description": "dual 3-lane carriageways with emergency shoulders"
            }}

            JSON Output:
            """
        }

    def _update_stats_on_return(self, service_name: str, start_time: float, result: Optional[Dict]):
        duration = time.perf_counter() - start_time
        self.call_stats[service_name]["total_time_s"] += duration
        if result and not result.get("error"):
            self.call_stats[service_name]["success"] += 1
            logger.info(f"{service_name.capitalize()} call successful in {duration:.2f}s.")
        else:
            self.call_stats[service_name]["errors"] += 1
            logger.warning(f"{service_name.capitalize()} call failed or returned error after {duration:.2f}s. Result: {result}")


    async def _call_deepseek(self, prompt: str) -> Optional[Dict[str, Any]]:
        service_name = "deepseek"
        api_key = self.deepseek_config.get("api_key")
        base_url = self.deepseek_config.get("base_url")

        if not api_key or api_key == "YOUR_DEEPSEEK_API_KEY":
            logger.warning("DeepSeek API key not configured or is placeholder. Skipping DeepSeek call.")
            return {"error": "DeepSeek API key not configured"} # Return error dict

        if not base_url:
            logger.warning("DeepSeek base URL not configured. Skipping DeepSeek call.")
            return {"error": "DeepSeek base URL not configured"}


        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024, "temperature": 0.7}

        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()
        last_exception_info = None
        response_text_for_logging = None

        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempting DeepSeek call ({attempt + 1}/{self.max_retries + 1})...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{base_url}/v1/chat/completions", headers=headers, json=payload, timeout=30.0)
                    response_text_for_logging = response.text # Store for potential JSONDecodeError logging
                    response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx

                    result_json = response.json() # Can raise json.JSONDecodeError if response is not valid JSON

                    if result_json.get("choices") and result_json["choices"][0].get("message"):
                        content_str = result_json["choices"][0]["message"].get("content")
                        # Try to parse the content string which is expected to be JSON
                        parsed_content = json.loads(content_str) # Can also raise json.JSONDecodeError
                        self._update_stats_on_return(service_name, start_time, parsed_content)
                        return parsed_content

                    logger.error(f"Unexpected response structure from DeepSeek: {result_json}")
                    last_exception_info = {"error": "Unexpected response structure from DeepSeek", "details": result_json}
                    break # Non-retryable error structure

            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from DeepSeek response: {e}. Response text: '{response_text_for_logging[:500]}...'")
                last_exception_info = {"error": "JSON decode error", "details": str(e), "raw_response_snippet": response_text_for_logging[:500] if response_text_for_logging else "N/A"}
                break # Non-retryable error
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling DeepSeek: {e.response.status_code} - {e.response.text}", exc_info=False) # exc_info=False to avoid verbose traceback for common HTTP errors
                last_exception_info = {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
                if not (500 <= e.response.status_code < 600) and e.response.status_code != 429: # Retry on 5xx and 429 (rate limit)
                    break
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error calling DeepSeek: {e}", exc_info=False)
                last_exception_info = {"error": "Timeout error", "details": str(e)}
            except httpx.ConnectError as e:
                logger.error(f"Connection error calling DeepSeek (server down?): {e}", exc_info=False)
                last_exception_info = {"error": "Connection error", "details": str(e)}
                break # Usually not retryable immediately
            except httpx.RequestError as e: # Catch other httpx request errors
                logger.error(f"Request error calling DeepSeek: {e}", exc_info=False)
                last_exception_info = {"error": "Request error", "details": str(e)}
            except Exception as e: # Catch-all for unexpected errors
                logger.error(f"An unexpected error occurred with DeepSeek: {e}", exc_info=True)
                last_exception_info = {"error": "Unexpected error", "details": str(e)}
                break # Non-retryable for unknown errors

            if attempt < self.max_retries:
                logger.info(f"Waiting {self.retry_delay}s before retrying DeepSeek...")
                await asyncio.sleep(self.retry_delay)
            else: # Max retries reached
                logger.warning(f"Max retries reached for DeepSeek.")

        self._update_stats_on_return(service_name, start_time, last_exception_info)
        return last_exception_info


    async def _call_ollama(self, prompt: str, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        service_name = "ollama"
        ollama_base_url = self.ollama_config.get("base_url")
        if not ollama_base_url:
            logger.warning("Ollama base URL not configured. Skipping Ollama call.")
            return {"error": "Ollama base URL not configured"}

        effective_model_name = model_name or self.ollama_config.get("model", "llama2")
        payload = {"model": effective_model_name, "prompt": prompt, "stream": False, "format": "json"}

        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()
        last_exception_info = None
        response_text_for_logging = None # For logging raw response in case of JSON error

        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempting Ollama call ({attempt + 1}/{self.max_retries + 1}) to model '{effective_model_name}' at {ollama_base_url}...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{ollama_base_url}/api/generate", json=payload, timeout=60.0)
                    response_text_for_logging = response.text # Store for potential JSONDecodeError logging
                    response.raise_for_status()

                    result_json = response.json() # Can raise json.JSONDecodeError
                    result_text_field = result_json.get("response")

                    if result_text_field:
                        # The 'response' field from Ollama (with format:json) should be a JSON string
                        parsed_content = json.loads(result_text_field) # Can raise json.JSONDecodeError
                        self._update_stats_on_return(service_name, start_time, parsed_content)
                        return parsed_content

                    logger.error(f"Empty or unexpected 'response' field from Ollama model '{effective_model_name}'. Details: {result_json}")
                    last_exception_info = {"error": "Empty or malformed 'response' field from Ollama", "details": result_json}
                    break # Non-retryable structure error

            except json.JSONDecodeError as e:
                # This can happen if response.json() fails or if json.loads(result_text_field) fails
                raw_response_content = result_text_field if 'result_text_field' in locals() and result_text_field is not None else response_text_for_logging
                logger.error(f"Error decoding JSON from Ollama model '{effective_model_name}' response: {e}. Response text: '{str(raw_response_content)[:500]}...'")
                last_exception_info = {"error": "JSON decode error", "details": str(e), "raw_response_snippet": str(raw_response_content)[:500] if raw_response_content else "N/A"}
                break # Non-retryable error
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling Ollama model '{effective_model_name}': {e.response.status_code} - {e.response.text}", exc_info=False)
                last_exception_info = {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
                if not (500 <= e.response.status_code < 600) and e.response.status_code != 429:
                    break
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error calling Ollama model '{effective_model_name}': {e}", exc_info=False)
                last_exception_info = {"error": "Timeout error", "details": str(e)}
            except httpx.ConnectError as e:
                logger.error(f"Connection error calling Ollama (is Ollama server running at {ollama_base_url}?): {e}", exc_info=False)
                last_exception_info = {"error": "Connection error (Ollama server unreachable?)", "details": str(e)}
                break # Usually not retryable immediately
            except httpx.RequestError as e:
                logger.error(f"Request error calling Ollama model '{effective_model_name}': {e}", exc_info=False)
                last_exception_info = {"error": "Request error", "details": str(e)}
            except Exception as e:
                logger.error(f"An unexpected error occurred with Ollama model '{effective_model_name}': {e}", exc_info=True)
                last_exception_info = {"error": "Unexpected error", "details": str(e)}
                break

            if attempt < self.max_retries:
                logger.info(f"Waiting {self.retry_delay}s before retrying Ollama model '{effective_model_name}'...")
                await asyncio.sleep(self.retry_delay)
            else:
                logger.warning(f"Max retries reached for Ollama model '{effective_model_name}'.")

        self._update_stats_on_return(service_name, start_time, last_exception_info)
        return last_exception_info

    async def _call_qwen(self, prompt: str) -> Optional[Dict[str, Any]]:
        service_name = "qwen"
        # Qwen is currently mocked. If it were a real API call, it would need similar error handling.
        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()

        # model_path = self.qwen_config.get("model_path") # From config, already env-aware
        logger.info("Using Qwen mock placeholder response (actual call not implemented).")

        user_input_marker = 'User Requirements: "'
        prompt_start_index = prompt.find(user_input_marker)
        user_input = "generic input"
        if prompt_start_index != -1:
            prompt_start_index += len(user_input_marker)
            prompt_end_index = prompt.find('"', prompt_start_index)
            if prompt_end_index != -1: user_input = prompt[prompt_start_index:prompt_end_index][:100]

        mock_response = {
            "bridge_type_preference": "Mocked Qwen Type (e.g., Beam Bridge if 'beam' in input)",
            "span_length_description": f"Mocked Qwen Span for '{user_input}' (e.g., 50m)",
            "load_requirements": "Mocked Qwen Load (e.g., Standard Highway)",
            # ... other fields ...
            "source_model": "qwen_mock_placeholder"
        }
        # Simulate potential error for testing failover
        # if "error_qwen" in prompt:
        #     self._update_stats_on_return(service_name, start_time, {"error": "Simulated Qwen error"})
        #     return {"error": "Simulated Qwen error"}

        self._update_stats_on_return(service_name, start_time, mock_response)
        return mock_response

    def get_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        template = self.prompt_templates.get(template_name)
        if not template:
            logger.error(f"Prompt template '{template_name}' not found.")
            return None
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing argument {e} for prompt template '{template_name}'.")
            return None


    async def analyze_text_with_failover(self, text_to_analyze: str, prompt_template_name: str = "extract_bridge_parameters") -> Tuple[Optional[Dict[str, Any]], str]:
        logger.info(f"Starting LLM analysis for text: '{text_to_analyze[:100]}...' using template '{prompt_template_name}'")
        prompt = self.get_prompt(prompt_template_name, user_input=text_to_analyze)
        if not prompt:
            return {"error": "Failed to generate prompt from template"}, "system"

        # Attempt DeepSeek
        # No explicit check for api_key here, _call_deepseek handles it and returns error dict if not configured
        logger.info("Attempting analysis with DeepSeek...")
        deepseek_result = await self._call_deepseek(prompt)
        if deepseek_result and not deepseek_result.get("error"):
            # Success logging is now part of _update_stats_on_return
            return deepseek_result, "DeepSeek"
        # Failure/error logging is part of _update_stats_on_return or _call_deepseek

        # Attempt Ollama
        logger.info("Attempting analysis with Ollama...")
        ollama_result = await self._call_ollama(prompt)
        if ollama_result and not ollama_result.get("error"):
            return ollama_result, "Ollama"

        # Attempt Qwen (mocked)
        logger.info("Attempting analysis with Qwen (mock)...")
        qwen_result = await self._call_qwen(prompt) # Qwen is mocked, less likely to fail unless simulated
        if qwen_result and not qwen_result.get("error"):
            return qwen_result, "Qwen"

        logger.error("All LLM providers failed for text analysis.")
        return {"error": "All LLM providers failed or returned errors.",
                "deepseek_attempt_result": deepseek_result, # Include results of attempts for debugging
                "ollama_attempt_result": ollama_result,
                "qwen_attempt_result": qwen_result
               }, "none"

    def get_call_statistics(self) -> Dict:
        """Returns the collected call statistics."""
        return self.call_stats

    def log_call_statistics(self):
        """Logs the collected call statistics."""
        logger.info("LLM Call Statistics:")
        for service, stats in self.call_stats.items():
            avg_time = (stats["total_time_s"] / stats["success"]) if stats["success"] > 0 else 0
            logger.info(f"  {service.capitalize()}: Attempts={stats['attempts']}, Success={stats['success']}, Errors={stats['errors']}, "
                        f"TotalTime={stats['total_time_s']:.2f}s, AvgTimePerSuccess={avg_time:.2f}s")


async def main_test():
    # Ensure .env is loaded for standalone testing
    from dotenv import load_dotenv
    load_dotenv()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Running LLM Service Standalone Test ---")
    # Re-initialize LLMService to pick up .env changes if any, as LLM_CONFIG is read at import time.
    # This is a bit tricky; ideally, config is dynamically fetched or service reinitialized.
    # For this test, assume config.py's load_dotenv and os.getenv did their job before LLMService init.
    llm_service = LLMService(max_retries=1, retry_delay=0.2)


    test_prompt_gen = llm_service.get_prompt("extract_bridge_parameters", user_input="Design a very long bridge for trains over a wide river.")
    if test_prompt_gen:
        logger.info(f"Generated Prompt Example:\n{test_prompt_gen[:200]}...")

    logger.info("Testing text analysis with failover...")
    analysis_input = "I need a sturdy pedestrian bridge to cross a small canyon, approximately 50 meters long. Aesthetics are important, something modern."

    # To test specific scenarios, you might modify config values before calling analyze_text_with_failover
    # For example, to simulate DeepSeek key missing and Ollama down:
    # original_deepseek_key = llm_service.deepseek_config.get("api_key")
    # original_ollama_url = llm_service.ollama_config.get("base_url")
    # logger.info("Simulating DeepSeek API key not configured and Ollama server down for this test run...")
    # llm_service.deepseek_config["api_key"] = "YOUR_DEEPSEEK_API_KEY" # Simulate placeholder
    # llm_service.ollama_config["base_url"] = "http://localhost:1111" # Simulate wrong port

    result, provider = await llm_service.analyze_text_with_failover(analysis_input)

    # Restore original config if changed for test
    # llm_service.deepseek_config["api_key"] = original_deepseek_key
    # llm_service.ollama_config["base_url"] = original_ollama_url

    logger.info(f"Standalone Test Analysis Result from Provider '{provider}':")
    if result:
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        logger.warning("No result obtained from standalone test.")

    llm_service.log_call_statistics() # Log stats at the end of the test
    logger.info("--- LLM Service Standalone Test Finished ---")

if __name__ == "__main__":
    # Add project root to sys.path for standalone execution, allowing imports like 'config'
    # This is already done at the top of the file.

    # The main_test function now includes load_dotenv.
    asyncio.run(main_test())
