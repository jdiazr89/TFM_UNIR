# app/schemas.py
# Definiciones de contratos de entrada y salida de la API.
# Estos modelos validan estructura y tipos automáticamente en FastAPI.
from pydantic import BaseModel
from typing import List, Dict


class ChatRequest(BaseModel):
    # Identificador del usuario que segmenta memoria conversacional.
    user_id: str
    # Mensaje libre enviado por el cliente.
    message: str


class ChatResponse(BaseModel):
    # Texto final que el asistente devuelve al frontend.
    reply: str
    # True si se inyectó memoria recuperada para responder.
    used_memory: bool
    # Fragmentos de memoria recuperados para trazabilidad.
    retrieved_memories: List[str]


class EvaluationRequest(BaseModel):
    # Usuario sintético usado en evaluación.
    user_id: str
    # Identificador del escenario evaluado.
    scenario_id: str
    # Conversación completa del escenario.
    messages: List[str]


class EvaluationResult(BaseModel):
    # Escenario al que pertenecen estos resultados.
    scenario_id: str
    # Respuestas generadas cuando la memoria está activa.
    with_memory: List[str]
    # Respuestas generadas sin usar memoria contextual.
    without_memory: List[str]
    # Métricas resumidas de comparación.
    metrics: Dict[str, float]
