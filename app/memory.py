# Capa de memoria persistente basada en ChromaDB.
# Aquí se guarda el historial conversacional y se recupera por similitud semántica.
import chromadb
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from typing import List
import re
import os
import uuid
from datetime import datetime, timezone
from typing import Dict

class VectorMemory:
    # Encoder compartido entre instancias para evitar recargas costosas.
    _shared_encoder: SentenceTransformer | None = None

    def __init__(self, collection_name: str = "memories", embedding_model: str = "all-MiniLM-L6-v2"):

        # Crear carpeta si no existe
        os.makedirs("vector_memory", exist_ok=True)

        # Nuevo cliente persistente (API moderna)
        self.client = PersistentClient(path="vector_memory")

        # Crear colección si no existe
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # recomendado
        )

        # Modelo de embeddings (se carga de forma diferida para acelerar arranque)
        self.embedding_model = embedding_model

    def _get_encoder(self) -> SentenceTransformer:
        # Lazy-loading: se carga solo cuando realmente se necesita embebido.
        if VectorMemory._shared_encoder is None:
            VectorMemory._shared_encoder = SentenceTransformer(self.embedding_model)
        return VectorMemory._shared_encoder

    def _embed(self, text: str):
        # Convierte texto a vector numérico compatible con Chroma.
        encoder = self._get_encoder()
        return encoder.encode([text])[0].tolist()

    @staticmethod
    def _extract_timestamp(doc: str) -> str:
        """Extrae timestamp ISO en formato [ts:...], si existe."""
        match = re.search(r"\[ts:([^\]]+)\]", doc)
        return match.group(1) if match else ""

    def store_memory(self, user_id: str, message: str, reply: str, tipo: str = "chat", extra: dict | None = None):
        # Metadatos mínimos para filtrar por usuario y tipo de interacción.

        metadata = {
            "user_id": user_id,
            "tipo": tipo
        }

        if extra:
            # Campos adicionales opcionales (ejemplo: número de pedido).
            metadata.update(extra)

        # Timestamp explícito para que el LLM pueda resolver contradicciones por recencia.
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Documento canónico: turno de usuario + respuesta del asistente.
        doc = f"[ts:{ts}] Usuario: {message}\nCompita: {reply}"
        embedding = self._embed(doc)

        self.collection.add(
            documents=[doc],
            embeddings=[embedding],
            metadatas=[metadata],
            # UUID evita colisiones e impide depender del count global.
            ids=[f"{user_id}_{uuid.uuid4().hex}"]
        )

    def retrieve_memories(self, user_id: str, query: str, top_k: int = 3) -> List[str]:
        # Guard clause para evitar consultas inválidas.
        if top_k <= 0:
            return []

        embedding = self._embed(query)

        results = self.collection.query(
            query_embeddings=[embedding],
            # Mantener orden de similitud semántica evita ruido por recencia irrelevante.
            n_results=top_k,
            # Nunca mezclar memoria entre usuarios.
            where={"user_id": user_id}
        )

        docs = results.get("documents", [[]])[0]
        if not docs:
            return []
        return docs

    def get_last_order_for_user(self, user_id: str) -> str | None:
        # Búsqueda acotada a tipo 'pedido' para recuperar el último número usado.

        results = self.collection.query(
            query_texts=["pedido"],
            n_results=5,
            where={"user_id": user_id, "tipo": "pedido"}
        )

        docs = results.get("documents", [[]])[0]
        if not docs:
            return None

        # Se recorre en reversa para priorizar memorias más recientes.
        for doc in reversed(docs):
            match = re.search(r"#(\d{5,10})", doc)
            if match:
                return match.group(1)

        return None

    def store_fact(self, user_id: str, fact_key: str, fact_value: str) -> None:
        """Guarda un hecho estructurado del usuario para recuperación determinista."""
        self.store_memory(
            user_id=user_id,
            message=f"FACT {fact_key}: {fact_value}",
            reply="fact_stored",
            tipo="fact",
            extra={"fact_key": fact_key, "fact_value": fact_value}
        )

    def get_latest_fact(self, user_id: str, fact_key: str) -> str | None:
        """Obtiene el valor más reciente de una clave de hecho para un usuario."""
        results = self.collection.query(
            query_texts=[fact_key],
            n_results=10,
            where={"user_id": user_id, "tipo": "fact", "fact_key": fact_key}
        )

        metadatas = results.get("metadatas", [[]])[0]
        if metadatas:
            for meta in reversed(metadatas):
                value = meta.get("fact_value") if isinstance(meta, dict) else None
                if value:
                    return str(value)

        docs = results.get("documents", [[]])[0]
        for doc in reversed(docs):
            match = re.search(rf"FACT\s+{re.escape(fact_key)}:\s*(.*)", doc)
            if match:
                return match.group(1).strip()
        return None

    def get_latest_facts(self, user_id: str, fact_keys: List[str]) -> Dict[str, str]:
        """Devuelve un diccionario key->value con los hechos más recientes disponibles."""
        facts: Dict[str, str] = {}
        for key in fact_keys:
            value = self.get_latest_fact(user_id, key)
            if value:
                facts[key] = value
        return facts
