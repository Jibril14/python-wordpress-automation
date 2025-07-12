# openai_api.py
import requests

# def generate_text(model: str = "llama3.2:latest", prompt: str) -> str:
def generate_text(prompt: str, model: str = "llama3.2:latest") -> str:
    """Generate text using Ollama's local API."""
    payload = {
        "prompt": prompt,
        "model": model,
        "stream": False
    }

    try:
        response = requests.post("http://localhost:11434/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.RequestException as e:
        print(f"❌ Ollama request failed: {e}")
        return ""
