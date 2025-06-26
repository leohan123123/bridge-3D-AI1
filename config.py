# Configuration management

LLM_CONFIG = {
    "deepseek": {"api_key": "YOUR_DEEPSEEK_API_KEY", "base_url": "https://api.deepseek.com"},
    "ollama": {"base_url": "http://localhost:11434", "model": "llama2"}, # Default model for Ollama
    "qwen": {"model_path": "./models/qwen2.5-14b"} # Placeholder path
}

# Example of how to access configuration
if __name__ == "__main__":
    print("LLM Configuration:")
    for provider, settings in LLM_CONFIG.items():
        print(f"  {provider}: {settings}")

    print("\nTo use DeepSeek, please replace 'YOUR_DEEPSEEK_API_KEY' with your actual API key.")
    print("Ensure your local Ollama service is running at the specified base_url.")
    print("For Qwen, update 'model_path' if your model is located elsewhere or you are using an API.")
