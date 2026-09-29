# Cliente mínimo para invocar Ollama por HTTP.
# Se mantiene como clase para encapsular configuración y reutilizar sesión.
import requests

class LLMClient:
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434", timeout_seconds: int = 60):
        # Modelo objetivo en Ollama (por ejemplo, llama3.1).
        self.model_name = model_name
        # URL base normalizada para evitar doble slash al concatenar rutas.
        self.base_url = base_url.rstrip("/")
        # Timeout global por solicitud de generación.
        self.timeout_seconds = timeout_seconds
        # Session reduce overhead al reutilizar conexiones TCP.
        self.session = requests.Session()

    def generate(self, prompt: str) -> str:
        # Request sin streaming para simplificar la integración en API síncrona.
        response = self.session.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "num_predict": 256,  # ⚡ límite para acelerar
                "temperature": 0.7,
                # Mantiene el modelo caliente en memoria para reducir latencia.
                "keep_alive": "10m"
            },
            timeout=self.timeout_seconds
        )
        # Si Ollama responde con error, propagamos excepción HTTP explícita.
        response.raise_for_status()
        # Extraemos solo el texto generado.
        return response.json().get("response", "")
