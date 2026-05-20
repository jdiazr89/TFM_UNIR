# eval/eval_memory_vs_nomemory.py
import requests

BASE_URL = "http://127.0.0.1:8000/api"


def run_scenario():
    payload = {
        "user_id": "usuario_demo",
        "scenario_id": "escenario_1",
        "messages": [
            "Hola, soy Junior y estoy haciendo una maestría.",
            "¿Puedes recordarme qué estoy estudiando?",
            "Dame una recomendación para mejorar mi proyecto."
        ]
    }

    resp = requests.post(f"{BASE_URL}/evaluate", json=payload)
    print(resp.json())


if __name__ == "__main__":
    run_scenario()
