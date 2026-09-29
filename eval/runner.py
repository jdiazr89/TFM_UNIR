# eval/runner.py
# Runner de evaluación robusta para comparar chatbot con memoria vs sin memoria.
# Ejecuta escenarios multivuelta, aplica checks objetivos y genera reportes.
import csv
import json
import os
import time
import unicodedata
from typing import Any, Dict, List, Tuple

import requests

try:
    from scenarios import scenarios
except ImportError:
    # Permite ejecutar desde la raíz como: python eval/runner.py
    from eval.scenarios import scenarios


BASE_URL = "http://127.0.0.1:8000/api"
HEALTHCHECK_URL = "http://127.0.0.1:8000/docs"
REQUEST_TIMEOUT_SECONDS = 180
STARTUP_MAX_WAIT_SECONDS = 120
MAX_RETRIES_PER_SCENARIO = 2
RETRY_BACKOFF_SECONDS = 4


def wait_for_api_ready(max_wait_seconds: int = STARTUP_MAX_WAIT_SECONDS) -> bool:
    # Espera activa del backend para evitar fallos por arranque en frío.
    start = time.time()
    while (time.time() - start) < max_wait_seconds:
        try:
            response = requests.get(HEALTHCHECK_URL, timeout=3)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    return False


def normalize_text(text: str) -> str:
    # Normaliza para matching robusto: minúsculas y sin diacríticos.
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def contains_any_term(text: str, terms: List[str]) -> bool:
    # Evalúa si al menos un término esperado aparece en la respuesta.
    norm_text = normalize_text(text)
    return any(normalize_text(term) in norm_text for term in terms)


def evaluate_last_response(last_response: str, checks: Dict[str, Any]) -> Dict[str, Any]:
    # Convierte reglas declarativas del escenario en un score numérico [0,1].
    total_checks = 0
    passed_checks = 0
    failed_rules: List[str] = []

    include_any = checks.get("last_response_must_include_any", [])
    if include_any:
        total_checks += 1
        if contains_any_term(last_response, include_any):
            passed_checks += 1
        else:
            failed_rules.append("last_response_must_include_any")

    exclude_any = checks.get("last_response_must_not_include_any", [])
    if exclude_any:
        total_checks += 1
        if not contains_any_term(last_response, exclude_any):
            passed_checks += 1
        else:
            failed_rules.append("last_response_must_not_include_any")

    must_ask_question = checks.get("must_ask_question")
    if must_ask_question is not None:
        total_checks += 1
        has_question = "?" in last_response or "¿" in last_response
        if bool(has_question) == bool(must_ask_question):
            passed_checks += 1
        else:
            failed_rules.append("must_ask_question")

    score = (passed_checks / total_checks) if total_checks else 0.0
    return {
        "score": round(score, 4),
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "failed_rules": failed_rules,
    }


def run_scenario(scenario: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    # user_id único por corrida para aislar contaminación entre escenarios.
    user_id = f"eval_{scenario['scenario_id']}_{run_id}"

    payload = {
        "user_id": user_id,
        "scenario_id": scenario["scenario_id"],
        "messages": scenario["messages"],
    }

    last_exc: Exception | None = None
    result: Dict[str, Any] = {}

    # Reintentos con backoff para tolerar fallos transitorios de red/modelo.
    for attempt in range(MAX_RETRIES_PER_SCENARIO + 1):
        try:
            resp = requests.post(
                f"{BASE_URL}/evaluate",
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            result = resp.json()
            break
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= MAX_RETRIES_PER_SCENARIO:
                raise
            time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))

    if not result:
        raise RuntimeError(f"No se recibió resultado del escenario: {scenario['scenario_id']}") from last_exc

    with_memory_responses = result.get("with_memory", [])
    without_memory_responses = result.get("without_memory", [])
    with_memory_last = with_memory_responses[-1] if with_memory_responses else ""
    without_memory_last = without_memory_responses[-1] if without_memory_responses else ""

    checks = scenario.get("checks", {})
    with_eval = evaluate_last_response(with_memory_last, checks)
    without_eval = evaluate_last_response(without_memory_last, checks)

    return {
        "scenario_id": scenario["scenario_id"],
        "category": scenario.get("category", "unknown"),
        "memory_advantage_expected": scenario.get("memory_advantage_expected", "unknown"),
        "messages": scenario["messages"],
        "expected_behavior": scenario.get("expected_behavior", ""),
        "checks": checks,
        "with_memory_last_response": with_memory_last,
        "without_memory_last_response": without_memory_last,
        "with_memory_score": with_eval["score"],
        "without_memory_score": without_eval["score"],
        "score_delta": round(with_eval["score"] - without_eval["score"], 4),
        "with_memory_passed_checks": with_eval["passed_checks"],
        "without_memory_passed_checks": without_eval["passed_checks"],
        "total_checks": with_eval["total_checks"],
        "with_memory_failed_rules": with_eval["failed_rules"],
        "without_memory_failed_rules": without_eval["failed_rules"],
        "api_metrics": result.get("metrics", {}),
        "raw_result": result,
    }


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Resume performance global y por categoría temática.
    if not results:
        return {
            "total_scenarios": 0,
            "avg_with_memory_score": 0.0,
            "avg_without_memory_score": 0.0,
            "avg_delta": 0.0,
            "wins_with_memory": 0,
            "wins_without_memory": 0,
            "ties": 0,
            "by_category": {},
        }

    avg_with = sum(r["with_memory_score"] for r in results) / len(results)
    avg_without = sum(r["without_memory_score"] for r in results) / len(results)
    avg_delta = avg_with - avg_without

    wins_with = sum(1 for r in results if r["with_memory_score"] > r["without_memory_score"])
    wins_without = sum(1 for r in results if r["without_memory_score"] > r["with_memory_score"])
    ties = len(results) - wins_with - wins_without

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in results:
        grouped.setdefault(item["category"], []).append(item)

    by_category: Dict[str, Dict[str, Any]] = {}
    for category, items in grouped.items():
        c_avg_with = sum(r["with_memory_score"] for r in items) / len(items)
        c_avg_without = sum(r["without_memory_score"] for r in items) / len(items)
        by_category[category] = {
            "count": len(items),
            "avg_with_memory_score": round(c_avg_with, 4),
            "avg_without_memory_score": round(c_avg_without, 4),
            "avg_delta": round(c_avg_with - c_avg_without, 4),
        }

    return {
        "total_scenarios": len(results),
        "avg_with_memory_score": round(avg_with, 4),
        "avg_without_memory_score": round(avg_without, 4),
        "avg_delta": round(avg_delta, 4),
        "wins_with_memory": wins_with,
        "wins_without_memory": wins_without,
        "ties": ties,
        "by_category": by_category,
    }


def save_csv(results: List[Dict[str, Any]], filename: str = "eval/results/results.csv") -> None:
    # Export tabular para análisis en Excel/BI.
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "scenario_id",
                "category",
                "expected_behavior",
                "with_memory_score",
                "without_memory_score",
                "score_delta",
                "with_memory_last_response",
                "without_memory_last_response",
                "failed_rules_with_memory",
                "failed_rules_without_memory",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r["scenario_id"],
                    r["category"],
                    r["expected_behavior"],
                    r["with_memory_score"],
                    r["without_memory_score"],
                    r["score_delta"],
                    r["with_memory_last_response"],
                    r["without_memory_last_response"],
                    ", ".join(r["with_memory_failed_rules"]),
                    ", ".join(r["without_memory_failed_rules"]),
                ]
            )


def save_json(payload: Dict[str, Any], filename: str = "eval/results/results.json") -> None:
    # Export completo y trazable (incluye respuestas crudas por escenario).
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)


def save_markdown_summary(summary: Dict[str, Any], filename: str = "eval/results/summary.md") -> None:
    # Resumen legible para informe técnico/TFM.
    lines = [
        "# Resumen de evaluación",
        "",
        f"- Escenarios ejecutados: {summary['total_scenarios']}",
        f"- Score promedio con memoria: {summary['avg_with_memory_score']}",
        f"- Score promedio sin memoria: {summary['avg_without_memory_score']}",
        f"- Delta promedio (con - sin): {summary['avg_delta']}",
        f"- Ganados por con memoria: {summary['wins_with_memory']}",
        f"- Ganados por sin memoria: {summary['wins_without_memory']}",
        f"- Empates: {summary['ties']}",
        "",
        "## Resultado por categoría",
        "",
        "| Categoría | Casos | Score con memoria | Score sin memoria | Delta |",
        "|---|---:|---:|---:|---:|",
    ]

    for category, data in sorted(summary["by_category"].items()):
        lines.append(
            f"| {category} | {data['count']} | {data['avg_with_memory_score']} | "
            f"{data['avg_without_memory_score']} | {data['avg_delta']} |"
        )

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def safe_run_all() -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    # Ejecuta toda la batería sin abortar la corrida ante un escenario fallido.
    run_id = str(int(time.time()))
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    if not wait_for_api_ready():
        return [], [{"scenario_id": "_global_", "error": "Backend no disponible en /docs"}]

    total = len(scenarios)
    for index, scenario in enumerate(scenarios, start=1):
        scenario_id = scenario.get("scenario_id", "unknown")
        print(f"[{index}/{total}] Ejecutando: {scenario_id}", flush=True)
        try:
            results.append(run_scenario(scenario, run_id=run_id))
            print(f"[{index}/{total}] OK: {scenario_id}", flush=True)
        except requests.RequestException as exc:
            print(f"[{index}/{total}] ERROR HTTP: {scenario_id} -> {exc}", flush=True)
            errors.append(
                {
                    "scenario_id": scenario_id,
                    "error": f"Error HTTP: {exc}",
                }
            )
        except Exception as exc:
            print(f"[{index}/{total}] ERROR: {scenario_id} -> {exc}", flush=True)
            errors.append(
                {
                    "scenario_id": scenario_id,
                    "error": f"Error inesperado: {exc}",
                }
            )

    return results, errors


if __name__ == "__main__":
    # Flujo principal de CLI: ejecutar, agregar y persistir reportes.
    os.makedirs("eval/results", exist_ok=True)

    scenario_results, execution_errors = safe_run_all()
    summary = aggregate_results(scenario_results)

    output_payload = {
        "summary": summary,
        "execution_errors": execution_errors,
        "scenarios": scenario_results,
    }

    save_csv(scenario_results)
    save_json(output_payload)
    save_markdown_summary(summary)

    print("Evaluación completada.")
    print("Archivos generados en eval/results/: results.csv, results.json, summary.md")
    if execution_errors:
        print(f"Escenarios con error: {len(execution_errors)}")
