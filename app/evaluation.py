# Módulo legacy de evaluación.
# Se mantiene como referencia histórica del pipeline con/sin memoria.
from typing import List, Dict
from pydantic import BaseModel

from memory import VectorMemory
from llm_client import LLMClient


class EvaluationResultModel(BaseModel):
    # Identificador del caso evaluado.
    scenario_id: str
    # Respuestas por turno cuando se usa memoria.
    with_memory: List[str]
    # Respuestas por turno sin memoria.
    without_memory: List[str]
    # Métricas agregadas del escenario.
    metrics: Dict[str, float]


class EvaluationPipeline:
    def __init__(self, llm_client: LLMClient, memory_manager: VectorMemory):
        # Dependencias inyectadas para facilitar reemplazo/mock en pruebas.
        self.llm_client = llm_client
        self.memory_manager = memory_manager

    def run_scenario(self, user_id: str, scenario_id: str, messages: List[str]) -> EvaluationResultModel:
        # Primera pasada: cada turno consulta memoria y luego guarda la interacción.
        with_memory_responses = []
        for msg in messages:
            memories = self.memory_manager.retrieve_memories(user_id, msg, top_k=3)
            prompt = self.llm_client.build_contextual_prompt(msg, memories)
            reply = self.llm_client.generate_response(prompt)
            with_memory_responses.append(reply)
            self.memory_manager.store_memory(user_id, msg, reply)

        # Segunda pasada: misma conversación, pero sin contexto almacenado.
        without_memory_responses = []
        for msg in messages:
            prompt = self.llm_client.build_contextual_prompt(msg, memories=[])
            reply = self.llm_client.generate_response(prompt)
            without_memory_responses.append(reply)

        # Métricas estáticas heredadas (no reflejan scoring objetivo moderno).
        metrics = {
            "continuidad_con_memoria": 0.9,
            "continuidad_sin_memoria": 0.5,
            "repeticion_con_memoria": 0.2,
            "repeticion_sin_memoria": 0.6,
            "eficiencia_con_memoria": 0.85,
            "eficiencia_sin_memoria": 0.6
        }

        return EvaluationResultModel(
            scenario_id=scenario_id,
            with_memory=with_memory_responses,
            without_memory=without_memory_responses,
            metrics=metrics
        )
