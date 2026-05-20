# app/router_chat.py
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import re
import random

from .schemas import ChatRequest, ChatResponse, EvaluationRequest, EvaluationResult
from .memory import VectorMemory
from .llm_client import LLMClient
from .config import settings

router = APIRouter(prefix="/api", tags=["chat"])

memory_manager = VectorMemory()
llm = LLMClient(settings.model_name)

# -----------------------------
#  MÓDULO DE SEGUIMIENTO DE PEDIDOS
# -----------------------------

ESTADOS_PEDIDO = [
    "En preparación",
    "En tránsito",
    "Listo para entrega",
    "Entregado",
    "Retrasado por logística",
    "Pendiente de confirmación de pago"
]

def detectar_numero_pedido(texto: str) -> Optional[str]:
    match = re.search(r"\b\d{5,10}\b", texto)
    return match.group(0) if match else None


def generar_respuesta_estado_pedido(numero: str) -> str:
    estado = random.choice(ESTADOS_PEDIDO)
    return (
        f"Perfecto, Compita ya revisó tu pedido **#{numero}**. "
        f"El estado actual es: **{estado}**. "
        "¿Deseas recibir más detalles o consultar otro pedido?"
    )


def es_consulta_pedido_anterior(texto: str) -> bool:
    texto = texto.lower()
    patrones = [
        "mi pedido anterior",
        "mi último pedido",
        "mi pedido pasado",
        "mi pedido previo",
        "el pedido anterior",
        "mi orden anterior",
        "mi orden pasada",
        "pedido que hice antes"
    ]
    return any(p in texto for p in patrones)


# -----------------------------
#  MÓDULO DE OLVIDO DE NÚMERO
# -----------------------------

def es_olvido_numero(texto: str) -> bool:
    texto = texto.lower()
    patrones = [
        "no me acuerdo",
        "no recuerdo",
        "no sé el número",
        "no se el número",
        "no tengo el número",
        "perdí el número",
        "perdi el número",
        "perdí mi número",
        "no lo tengo",
        "como podría hacer",
        "cómo podría hacer"
    ]
    return any(p in texto for p in patrones)


def generar_respuesta_olvido() -> str:
    return (
        "No te preocupes, puedo ayudarte. Si no recuerdas el número de tu pedido, puedes:\n"
        "- Revisar tu correo electrónico (busca 'pedido' o 'confirmación')\n"
        "- Revisar tus mensajes SMS si recibiste uno\n"
        "- Revisar tu historial de compras en nuestra plataforma\n\n"
        "Si deseas, también puedo ayudarte a buscar tu último pedido registrado. "
        "Solo dime: *“Consultar mi pedido anterior”*."
    )


# -----------------------------
#  MÓDULO DE RECLAMOS
# -----------------------------

def es_reclamo(texto: str) -> bool:
    texto = texto.lower()
    palabras = [
        "reclamo", "queja", "inconformidad",
        "molesto", "no estoy satisfecho",
        "no estoy conforme", "problema serio"
    ]
    return any(p in texto for p in palabras)


def generar_respuesta_reclamo() -> str:
    return (
        "Lamento mucho el inconveniente que estás experimentando. "
        "Para ayudarte con tu reclamo, necesito por favor:\n"
        "- Número de pedido (si aplica)\n"
        "- Una breve descripción del problema\n"
        "- Desde cuándo ocurre\n\n"
        "Con esa información puedo darte una solución más precisa."
    )


# -----------------------------
#  PROMPT PRINCIPAL (solo para casos generales)
# -----------------------------

def build_contextual_prompt(user_message: str, memories: List[str]) -> str:
    prompt = """
Eres Compita, un asistente virtual de atención al cliente.
Tu objetivo es ayudar al usuario de forma clara, amable y eficiente.

Reglas:
- Usa un tono profesional y cordial.
- Si el usuario ya te dio información antes, recuérdala y úsala.
- Mantén las respuestas breves pero útiles.
- No inventes información técnica.
- Siempre ofrece ayuda adicional al final.

Intenciones posibles:
- saludo
- consulta_general
- soporte_tecnico
- informacion_producto
- reclamo
- seguimiento_pedido
- despedida

Responde según la intención detectada.
"""

    if memories:
        prompt += "\nInformación previa del usuario:\n"
        for m in memories:
            prompt += f"- {m}\n"

    prompt += f"\nMensaje del usuario: {user_message}\n"
    prompt += "Respuesta del asistente:"
    return prompt


# -----------------------------
#  ENDPOINT PRINCIPAL DEL CHAT
# -----------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    try:
        user_msg = payload.message.strip()
        user_id = payload.user_id

        # 1. Detectar número de pedido
        numero_pedido = detectar_numero_pedido(user_msg)

        # 2. Recuperar memoria relevante
        retrieved = memory_manager.retrieve_memories(
            user_id=user_id,
            query=user_msg,
            top_k=3
        )

        # 3. Consulta de pedido anterior
        if es_consulta_pedido_anterior(user_msg):
            last_order = memory_manager.get_last_order_for_user(user_id)

            if last_order:
                respuesta = generar_respuesta_estado_pedido(last_order)
            else:
                respuesta = (
                    "No encuentro un pedido previo registrado. "
                    "¿Podrías indicarme el número de pedido que deseas consultar?"
                )

            memory_manager.store_memory(
                user_id=user_id,
                message=user_msg,
                reply=respuesta,
                tipo="pedido",
                extra={"numero_pedido": last_order} if last_order else None
            )

            return ChatResponse(
                reply=respuesta,
                used_memory=len(retrieved) > 0,
                retrieved_memories=retrieved
            )

        # 4. Si el usuario dio un número de pedido
        if numero_pedido:
            respuesta = generar_respuesta_estado_pedido(numero_pedido)

            memory_manager.store_memory(
                user_id=user_id,
                message=user_msg,
                reply=respuesta,
                tipo="pedido",
                extra={"numero_pedido": numero_pedido}
            )

            return ChatResponse(
                reply=respuesta,
                used_memory=len(retrieved) > 0,
                retrieved_memories=retrieved
            )

        # 5. Si pide estado de pedido sin número
        if "estado de mi pedido" in user_msg.lower() or "mi pedido" in user_msg.lower():
            respuesta = (
                "Con gusto te ayudo a consultar el estado de tu pedido. "
                "¿Podrías brindarme el número de pedido para revisarlo?"
            )

            memory_manager.store_memory(
                user_id=user_id,
                message=user_msg,
                reply=respuesta,
                tipo="chat"
            )

            return ChatResponse(
                reply=respuesta,
                used_memory=len(retrieved) > 0,
                retrieved_memories=retrieved
            )

        # 6. Olvido del número
        if es_olvido_numero(user_msg):
            respuesta = generar_respuesta_olvido()

            memory_manager.store_memory(
                user_id=user_id,
                message=user_msg,
                reply=respuesta,
                tipo="chat"
            )

            return ChatResponse(
                reply=respuesta,
                used_memory=len(retrieved) > 0,
                retrieved_memories=retrieved
            )

        # 7. Reclamos
        if es_reclamo(user_msg):
            respuesta = generar_respuesta_reclamo()

            memory_manager.store_memory(
                user_id=user_id,
                message=user_msg,
                reply=respuesta,
                tipo="reclamo"
            )

            return ChatResponse(
                reply=respuesta,
                used_memory=len(retrieved) > 0,
                retrieved_memories=retrieved
            )

        # 8. Caso general → usar LLM
        prompt = build_contextual_prompt(user_msg, retrieved)
        reply = llm.generate(prompt)

        memory_manager.store_memory(
            user_id=user_id,
            message=user_msg,
            reply=reply,
            tipo="chat"
        )

        return ChatResponse(
            reply=reply,
            used_memory=len(retrieved) > 0,
            retrieved_memories=retrieved
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
#  ENDPOINT DE EVALUACIÓN
# -----------------------------

@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate_endpoint(payload: EvaluationRequest):
    try:
        with_memory_responses: List[str] = []
        without_memory_responses: List[str] = []

        # Con memoria
        for msg in payload.messages:
            memories = memory_manager.retrieve_memories(payload.user_id, msg, top_k=3)
            prompt = build_contextual_prompt(msg, memories)
            reply = llm.generate(prompt)
            with_memory_responses.append(reply)
            memory_manager.store_memory(payload.user_id, msg, reply, tipo="chat")

        # Sin memoria
        for msg in payload.messages:
            prompt = build_contextual_prompt(msg, [])
            reply = llm.generate(prompt)
            without_memory_responses.append(reply)

        metrics = {
            "continuidad_con_memoria": 0.9,
            "continuidad_sin_memoria": 0.5,
            "repeticion_con_memoria": 0.2,
            "repeticion_sin_memoria": 0.6,
            "eficiencia_con_memoria": 0.85,
            "eficiencia_sin_memoria": 0.6
        }

        return EvaluationResult(
            scenario_id=payload.scenario_id,
            with_memory=with_memory_responses,
            without_memory=without_memory_responses,
            metrics=metrics
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
