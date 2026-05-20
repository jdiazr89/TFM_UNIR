# app/schemas.py
from pydantic import BaseModel
from typing import List, Dict


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    used_memory: bool
    retrieved_memories: List[str]


class EvaluationRequest(BaseModel):
    user_id: str
    scenario_id: str
    messages: List[str]


class EvaluationResult(BaseModel):
    scenario_id: str
    with_memory: List[str]
    without_memory: List[str]
    metrics: Dict[str, float]
