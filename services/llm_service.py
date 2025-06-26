import httpx # For making HTTP requests to LLM APIs
from config import LLM_CONFIG # Import configurations
import json
import subprocess # For local Ollama CLI calls if needed (alternative to HTTP)
from typing import Dict, Any, Optional, Tuple

class LLMService:
    def __init__(self):
        self.deepseek_config = LLM_CONFIG.get("deepseek", {})
        self.ollama_config = LLM_CONFIG.get("ollama", {})
        self.qwen_config = LLM_CONFIG.get("qwen", {}) # Assuming Qwen might be local or API based

        # Basic prompt template example
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
            - environmental_factors (e.g., "high winds", "earthquake zone")

            Example of desired JSON output:
            {{
                "bridge_type_preference": "cable-stayed",
                "span_length_description": "long river crossing, about 500m",
                "load_requirements": "heavy vehicles and future light rail",
                "site_terrain": "over water, coastal area",
                "specific_materials": "corrosion-resistant steel and concrete",
                "budget_constraints": null,
                "aesthetic_preferences": "iconic and modern",
                "environmental_factors": "high winds, saltwater environment"
            }}

            JSON Output:
            """
        }

    async def _call_deepseek(self, prompt: str) -> Optional[Dict[str, Any]]:
        if not self.deepseek_config.get("api_key") or self.deepseek_config["api_key"] == "YOUR_DEEPSEEK_API_KEY":
            print("DeepSeek API key not configured. Skipping DeepSeek call.")
            return None

        headers = {
            "Authorization": f"Bearer {self.deepseek_config['api_key']}",
            "Content-Type": "application/json"
        }
        # Adjust model name as per DeepSeek's offerings, e.g., 'deepseek-chat' or 'deepseek-coder'
        payload = {
            "model": "deepseek-chat", # Or other appropriate model
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024, # Adjust as needed
            "temperature": 0.7 # Adjust for creativity vs. predictability
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.deepseek_config['base_url']}/v1/chat/completions", # Verify exact endpoint from DeepSeek docs
                    headers=headers,
                    json=payload,
                    timeout=30.0 # seconds
                )
                response.raise_for_status() # Raise an exception for HTTP errors
                result = response.json()
                # Extract the content, structure might vary based on API version
                if result.get("choices") and result["choices"][0].get("message"):
                    content_str = result["choices"][0]["message"].get("content")
                    return json.loads(content_str) # Assuming LLM returns valid JSON string
                return {"error": "Unexpected response structure from DeepSeek", "details": result}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error calling DeepSeek: {e.response.status_code} - {e.response.text}")
            return {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
        except httpx.RequestError as e:
            print(f"Request error calling DeepSeek: {e}")
            return {"error": "Request error", "details": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from DeepSeek response: {e}")
            return {"error": "JSON decode error", "details": str(e), "raw_response": content_str if 'content_str' in locals() else "N/A"}
        except Exception as e:
            print(f"An unexpected error occurred with DeepSeek: {e}")
            return {"error": "Unexpected error", "details": str(e)}

    async def _call_ollama(self, prompt: str, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ollama_base_url = self.ollama_config.get("base_url")
        if not ollama_base_url:
            print("Ollama base URL not configured. Skipping Ollama call.")
            return None

        # Use provided model_name or default from config, or a general default
        effective_model_name = model_name or self.ollama_config.get("model", "llama2")

        payload = {
            "model": effective_model_name,
            "prompt": prompt,
            "stream": False, # Get the full response at once
            "format": "json" # Request JSON output if supported by the model and Ollama version
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{ollama_base_url}/api/generate", # Standard Ollama generate endpoint
                    json=payload,
                    timeout=60.0 # Local models can be slower
                )
                response.raise_for_status()
                result_text = response.json().get("response")
                if result_text:
                    return json.loads(result_text) # Assuming the model's response string is valid JSON
                return {"error": "Empty response content from Ollama", "details": response.json()}
        except httpx.HTTPStatusError as e:
            print(f"HTTP error calling Ollama: {e.response.status_code} - {e.response.text}")
            return {"error": "HTTP error", "status_code": e.response.status_code, "details": e.response.text}
        except httpx.RequestError as e:
            # This catches network errors, like Ollama server not running
            print(f"Request error calling Ollama (is Ollama server running at {ollama_base_url}?): {e}")
            return {"error": "Request error (Ollama server unreachable?)", "details": str(e)}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama response: {e}")
            return {"error": "JSON decode error", "details": str(e), "raw_response": result_text if 'result_text' in locals() else "N/A"}
        except Exception as e:
            print(f"An unexpected error occurred with Ollama: {e}")
            return {"error": "Unexpected error", "details": str(e)}

    async def _call_qwen(self, prompt: str) -> Optional[Dict[str, Any]]:
        # This is a placeholder. Qwen integration depends on how it's hosted.
        # If it's a local model via a CLI or custom Python script:
        model_path = self.qwen_config.get("model_path")
        if not model_path:
            print("Qwen model path not configured. Skipping Qwen call.")
            return None

        print(f"Placeholder: Qwen model at {model_path} would be called with prompt: '{prompt[:100]}...'")
        # Example: Simulate calling a local script that interacts with Qwen
        # try:
        #     process = subprocess.run(
        #         ["python", "run_qwen_model.py", "--prompt", prompt], # Fictional script
        #         capture_output=True, text=True, check=True, timeout=120
        #     )
        #     return json.loads(process.stdout)
        # except FileNotFoundError:
        #     return {"error": "Qwen runner script not found."}
        # except subprocess.CalledProcessError as e:
        #     return {"error": "Error running Qwen model", "details": e.stderr}
        # except json.JSONDecodeError as e:
        #     return {"error": "Error decoding Qwen JSON output", "details": str(e)}
        # except Exception as e:
        #     return {"error": f"Unexpected error with Qwen: {e}"}

        # If Qwen is exposed via an API (similar to DeepSeek or Ollama):
        # Implement httpx call similar to _call_deepseek or _call_ollama

        # Mock response for now
        return {"message": "Qwen integration is a placeholder.", "parameters_extracted": {"mock_qwen_param": "value"}}


    def get_prompt(self, template_name: str, **kwargs) -> Optional[str]:
        """
        Formats a prompt using a predefined template and provided arguments.
        """
        template = self.prompt_templates.get(template_name)
        if not template:
            print(f"Error: Prompt template '{template_name}' not found.")
            return None
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Error: Missing argument {e} for prompt template '{template_name}'.")
            return None

    async def analyze_text_with_failover(self, text_to_analyze: str, prompt_template_name: str = "extract_bridge_parameters") -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Analyzes text using a preferred LLM, with failover to other configured LLMs.
        Tries DeepSeek, then Ollama, then Qwen.
        Returns a tuple: (result_dict, provider_name_str)
        """
        prompt = self.get_prompt(prompt_template_name, user_input=text_to_analyze)
        if not prompt:
            return {"error": "Failed to generate prompt from template"}, "system"

        # 1. Try DeepSeek
        print("Attempting analysis with DeepSeek...")
        deepseek_result = await self._call_deepseek(prompt)
        if deepseek_result and not deepseek_result.get("error"):
            print("Successfully analyzed with DeepSeek.")
            return deepseek_result, "DeepSeek"
        print(f"DeepSeek analysis failed or incomplete. Result: {deepseek_result}")

        # 2. Try Ollama (if DeepSeek failed)
        print("Attempting analysis with Ollama...")
        # You might want to use a simpler prompt for local models if the full JSON one is too complex
        ollama_result = await self._call_ollama(prompt)
        if ollama_result and not ollama_result.get("error"):
            print("Successfully analyzed with Ollama.")
            return ollama_result, "Ollama"
        print(f"Ollama analysis failed or incomplete. Result: {ollama_result}")

        # 3. Try Qwen (if Ollama also failed)
        print("Attempting analysis with Qwen...")
        qwen_result = await self._call_qwen(prompt) # This is currently a placeholder
        if qwen_result and not qwen_result.get("error"):
            print("Successfully analyzed with Qwen (placeholder).")
            return qwen_result, "Qwen"
        print(f"Qwen analysis failed or incomplete. Result: {qwen_result}")

        print("All LLM providers failed.")
        return {"error": "All LLM providers failed or returned errors.",
                "deepseek_attempt": deepseek_result,
                "ollama_attempt": ollama_result,
                "qwen_attempt": qwen_result
               }, "none"

# Example usage (async context needed)
async def main_test():
    llm_service = LLMService()

    # Test prompt generation
    test_prompt = llm_service.get_prompt("extract_bridge_parameters", user_input="Design a very long bridge for trains over a wide river.")
    if test_prompt:
        print("\nGenerated Prompt:\n", test_prompt)

    # Test analysis with failover
    # Ensure your LLM_CONFIG in config.py is set up, especially DeepSeek API key for a real test
    # or that Ollama is running locally.
    print("\nTesting text analysis with failover...")
    analysis_input = "I need a sturdy pedestrian bridge to cross a small canyon, approximately 50 meters long. Aesthetics are important, something modern."

    # To actually test DeepSeek, replace 'YOUR_DEEPSEEK_API_KEY' in config.py
    # To test Ollama, ensure it's running: `ollama serve` and you have a model like `ollama pull llama2`

    # Temporarily disable DeepSeek for local testing if key is not set
    # original_deepseek_key = llm_service.deepseek_config.get("api_key")
    # if llm_service.deepseek_config.get("api_key") == "YOUR_DEEPSEEK_API_KEY":
    #    llm_service.deepseek_config["api_key"] = None # Disable for this test run

    result, provider = await llm_service.analyze_text_with_failover(analysis_input)

    # llm_service.deepseek_config["api_key"] = original_deepseek_key # Restore key if changed

    print(f"\nAnalysis Result from {provider}:")
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("No result obtained.")

if __name__ == "__main__":
    import asyncio
    # To run this test:
    # 1. Make sure config.py has your DeepSeek API key (or Ollama is running).
    # 2. Run `python -m services.llm_service` from the project root.
    #    (You might need to adjust PYTHONPATH if imports fail: `export PYTHONPATH=.`)
    print("Running LLM Service standalone test...")
    asyncio.run(main_test())
