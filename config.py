# Configuration management
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# This makes it available for all modules importing config.py
load_dotenv()

LLM_CONFIG = {
    "deepseek": {
        "api_key": os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY"),
        "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    },
    "ollama": {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llama2") # Default model for Ollama
    },
    "qwen": { # Qwen currently mocked, but can follow same pattern if API based
        "api_key": os.getenv("QWEN_API_KEY"),
        "base_url": os.getenv("QWEN_BASE_URL"),
        "model_path": os.getenv("QWEN_MODEL_PATH","./models/qwen2.5-14b") # Placeholder path if local
    }
}

# Example of how to access configuration
if __name__ == "__main__":
    print("LLM Configuration (values are from environment variables if set, otherwise defaults):")
    for provider, settings in LLM_CONFIG.items():
        print(f"  {provider}:")
        for key, value in settings.items():
            print(f"    {key}: {value}")

    print("\nNotes:")
    if LLM_CONFIG["deepseek"]["api_key"] == "YOUR_DEEPSEEK_API_KEY":
        print("- To use DeepSeek, ensure DEEPSEEK_API_KEY environment variable is set, or update it in your .env file.")
    print("- Ensure your local Ollama service is running at the specified base_url (or set OLLAMA_BASE_URL).")
    print("- For Qwen, update configuration if using an API or a different local model path.")
