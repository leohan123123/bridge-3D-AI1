# Ensure project root is in sys.path for standalone execution
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import httpx # For making HTTP requests to LLM APIs
from config import LLM_CONFIG # Import configurations
import json
import subprocess # For local Ollama CLI calls if needed (alternative to HTTP)
from typing import Dict, Any, Optional, Tuple
import asyncio # For sleep
import logging
import time # For performance counter

# Configure basic logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class LLMService:
    def __init__(self, max_retries=2, retry_delay=1):
        logger.info(f"Initializing LLMService with max_retries={max_retries}, retry_delay={retry_delay}s")
        self.deepseek_config = LLM_CONFIG.get("deepseek", {})
        self.ollama_config = LLM_CONFIG.get("ollama", {})
        self.qwen_config = LLM_CONFIG.get("qwen", {})
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
        if not self.deepseek_config.get("api_key") or self.deepseek_config["api_key"] == "YOUR_DEEPSEEK_API_KEY":
            logger.warning("DeepSeek API key not configured or is placeholder. Skipping DeepSeek call.")
            return None # Not counted as an attempt if skipped due to config

        headers = {"Authorization": f"Bearer {self.deepseek_config['api_key']}", "Content-Type": "application/json"}
        payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024, "temperature": 0.7}

        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()
        last_exception_info = None

        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempting DeepSeek call ({attempt + 1}/{self.max_retries + 1})...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{self.deepseek_config['base_url']}/v1/chat/completions", headers=headers, json=payload, timeout=30.0)
                    response.raise_for_status()
                    result = response.json()
                    if result.get("choices") and result["choices"][0].get("message"):
                        content_str = result["choices"][0]["message"].get("content")
                        parsed_content = json.loads(content_str)
                        self._update_stats_on_return(service_name, start_time, parsed_content)
                        return parsed_content
                    logger.error(f"Unexpected response structure from DeepSeek: {result}")
                    last_exception_info = {"error": "Unexpected response structure from DeepSeek", "details": result}
                    self._update_stats_on_return(service_name, start_time, last_exception_info)
                    return last_exception_info
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling DeepSeek: {e.response.status_code} - {e.response.text}", exc_info=True)
                last_exception_info = {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
                if not (500 <= e.response.status_code < 600):
                    self._update_stats_on_return(service_name, start_time, last_exception_info)
                    return last_exception_info
            except httpx.RequestError as e:
                logger.error(f"Request error calling DeepSeek: {e}", exc_info=True)
                last_exception_info = {"error": "Request error", "details": str(e)}
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from DeepSeek response: {e}", exc_info=True)
                last_exception_info = {"error": "JSON decode error", "details": str(e), "raw_response": locals().get('content_str', "N/A")}
                self._update_stats_on_return(service_name, start_time, last_exception_info)
                return last_exception_info
            except Exception as e:
                logger.error(f"An unexpected error occurred with DeepSeek: {e}", exc_info=True)
                last_exception_info = {"error": "Unexpected error", "details": str(e)}

            if attempt < self.max_retries:
                logger.info(f"Waiting {self.retry_delay}s before retrying DeepSeek...")
                await asyncio.sleep(self.retry_delay)

        self._update_stats_on_return(service_name, start_time, last_exception_info)
        return last_exception_info

    async def _call_ollama(self, prompt: str, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        service_name = "ollama"
        ollama_base_url = self.ollama_config.get("base_url")
        if not ollama_base_url:
            logger.warning("Ollama base URL not configured. Skipping Ollama call.")
            return None

        effective_model_name = model_name or self.ollama_config.get("model", "llama2")
        payload = {"model": effective_model_name, "prompt": prompt, "stream": False, "format": "json"}

        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()
        last_exception_info = None

        for attempt in range(self.max_retries + 1):
            logger.info(f"Attempting Ollama call ({attempt + 1}/{self.max_retries + 1}) to model '{effective_model_name}' at {ollama_base_url}...")
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(f"{ollama_base_url}/api/generate", json=payload, timeout=60.0)
                    response.raise_for_status()
                    result_text = response.json().get("response")
                    if result_text:
                        parsed_content = json.loads(result_text)
                        self._update_stats_on_return(service_name, start_time, parsed_content)
                        return parsed_content
                    logger.error(f"Empty response content from Ollama model '{effective_model_name}'. Details: {response.json()}")
                    last_exception_info = {"error": "Empty response content from Ollama", "details": response.json()}
                    self._update_stats_on_return(service_name, start_time, last_exception_info)
                    return last_exception_info
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling Ollama model '{effective_model_name}': {e.response.status_code} - {e.response.text}", exc_info=True)
                last_exception_info = {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
                if not (500 <= e.response.status_code < 600):
                    self._update_stats_on_return(service_name, start_time, last_exception_info)
                    return last_exception_info
            except httpx.RequestError as e:
                logger.error(f"Request error calling Ollama (is Ollama server running at {ollama_base_url}?): {e}", exc_info=True)
                last_exception_info = {"error": "Request error (Ollama server unreachable?)", "details": str(e)}
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from Ollama model '{effective_model_name}' response: {e}", exc_info=True)
                last_exception_info = {"error": "JSON decode error", "details": str(e), "raw_response": locals().get('result_text', "N/A")}
                self._update_stats_on_return(service_name, start_time, last_exception_info)
                return last_exception_info
            except Exception as e:
                logger.error(f"An unexpected error occurred with Ollama model '{effective_model_name}': {e}", exc_info=True)
                last_exception_info = {"error": "Unexpected error", "details": str(e)}

            if attempt < self.max_retries:
                logger.info(f"Waiting {self.retry_delay}s before retrying Ollama model '{effective_model_name}'...")
                await asyncio.sleep(self.retry_delay)

        self._update_stats_on_return(service_name, start_time, last_exception_info)
        return last_exception_info

    async def _call_qwen(self, prompt: str) -> Optional[Dict[str, Any]]:
        service_name = "qwen"
        self.call_stats[service_name]["attempts"] += 1
        start_time = time.perf_counter()

        model_path = self.qwen_config.get("model_path")
        # Always return the mock response for Qwen in this testing phase,
        # regardless of model_path, as actual Qwen call is not implemented.
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
            "site_terrain": "Mocked Qwen Terrain (e.g., Flat area)",
            "specific_materials": "Mocked Qwen Materials (e.g., Concrete, Steel)",
            "budget_constraints": "Mocked Qwen Budget (e.g., Medium)",
            "aesthetic_preferences": "Mocked Qwen Aesthetics (e.g., Functional)",
            "environmental_factors": "Mocked Qwen Environment (e.g., Moderate climate)",
            "source_model": "qwen_mock_placeholder"
        }
        self._update_stats_on_return(service_name, start_time, mock_response)
        return mock_response

    def get_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        # ... (same as before, no changes to this method)
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
        # ... (same as before, no changes to this method's core logic)
        logger.info(f"Starting LLM analysis for text: '{text_to_analyze[:100]}...' using template '{prompt_template_name}'")
        prompt = self.get_prompt(prompt_template_name, user_input=text_to_analyze)
        if not prompt:
            return {"error": "Failed to generate prompt from template"}, "system"

        logger.info("Attempting analysis with DeepSeek...")
        deepseek_result = await self._call_deepseek(prompt)
        if deepseek_result and not deepseek_result.get("error"):
            logger.info("Successfully analyzed with DeepSeek.") # This log is now part of _update_stats_on_return
            return deepseek_result, "DeepSeek"
        # logger.warning already part of _update_stats_on_return

        logger.info("Attempting analysis with Ollama...")
        ollama_result = await self._call_ollama(prompt)
        if ollama_result and not ollama_result.get("error"):
            # logger.info("Successfully analyzed with Ollama.")
            return ollama_result, "Ollama"

        logger.info("Attempting analysis with Qwen...")
        qwen_result = await self._call_qwen(prompt)
        if qwen_result and not qwen_result.get("error"):
            # logger.info("Successfully analyzed with Qwen.")
            return qwen_result, "Qwen"

        logger.error("All LLM providers failed for text analysis.")
        return {"error": "All LLM providers failed or returned errors.",
                "deepseek_attempt": deepseek_result,
                "ollama_attempt": ollama_result,
                "qwen_attempt": qwen_result
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Running LLM Service Standalone Test ---")
    llm_service = LLMService(max_retries=1, retry_delay=0.2)

    # ... (rest of main_test remains the same)
    test_prompt_gen = llm_service.get_prompt("extract_bridge_parameters", user_input="Design a very long bridge for trains over a wide river.")
    if test_prompt_gen:
        logger.info(f"Generated Prompt Example:\n{test_prompt_gen[:200]}...")

    logger.info("Testing text analysis with failover...")
    analysis_input = "I need a sturdy pedestrian bridge to cross a small canyon, approximately 50 meters long. Aesthetics are important, something modern."

    original_deepseek_key = llm_service.deepseek_config.get("api_key")
    original_ollama_url = llm_service.ollama_config.get("base_url")

    logger.info("Simulating DeepSeek API key not configured and Ollama server down for this test run...")
    llm_service.deepseek_config["api_key"] = None
    llm_service.ollama_config["base_url"] = "http://localhost:1111"

    result, provider = await llm_service.analyze_text_with_failover(analysis_input)

    llm_service.deepseek_config["api_key"] = original_deepseek_key
    llm_service.ollama_config["base_url"] = original_ollama_url

    logger.info(f"Standalone Test Analysis Result from Provider '{provider}':")
    if result:
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        logger.warning("No result obtained from standalone test.")

    llm_service.log_call_statistics() # Log stats at the end of the test
    logger.info("--- LLM Service Standalone Test Finished ---")

if __name__ == "__main__":
    # Add project root to sys.path for standalone execution, allowing imports like 'config'
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # Re-import config if it failed due to path initially (though previous import at top level might still hold if it worked once)
    # This is more for robustness if script is imported then run.
    try:
        from config import LLM_CONFIG
    except ImportError:
        print("Failed to re-import config. Ensure PYTHONPATH is set correctly or run from project root.")

    asyncio.run(main_test())
