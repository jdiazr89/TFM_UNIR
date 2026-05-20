import requests

class LLMClient:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "num_predict": 256,  # ⚡ límite para acelerar
                "temperature": 0.7
            }
        )
        return response.json().get("response", "")
