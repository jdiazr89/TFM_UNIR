# Script corto para ejecutar un solo escenario de manera manual.
import requests

try:
    from scenarios import scenarios
except ImportError:
    from eval.scenarios import scenarios

BASE_URL = "http://127.0.0.1:8000/api"


def run_scenario(index: int = 0):
    # Selecciona escenario por índice para pruebas rápidas.
    scenario = scenarios[index]

    payload = {
        # user_id diferenciado para no contaminar otras pruebas.
        "user_id": f"usuario_demo_single_{scenario['scenario_id']}",
        "scenario_id": scenario["scenario_id"],
        "messages": scenario["messages"],
    }

    resp = requests.post(f"{BASE_URL}/evaluate", json=payload, timeout=120)
    resp.raise_for_status()
    # Muestra respuesta completa del endpoint de evaluación.
    print(resp.json())


if __name__ == "__main__":
    run_scenario()
