import chromadb
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from typing import List
import re
import os

class VectorMemory:
    def __init__(self, collection_name: str = "memories"):

        # Crear carpeta si no existe
        os.makedirs("vector_memory", exist_ok=True)

        # Nuevo cliente persistente (API moderna)
        self.client = PersistentClient(path="vector_memory")

        # Crear colección si no existe
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # recomendado
        )

        # Modelo de embeddings
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

    def _embed(self, text: str):
        return self.encoder.encode([text])[0].tolist()

    def store_memory(self, user_id: str, message: str, reply: str, tipo: str = "chat", extra: dict | None = None):

        metadata = {
            "user_id": user_id,
            "tipo": tipo
        }

        if extra:
            metadata.update(extra)

        doc = f"Usuario: {message}\nCompita: {reply}"
        embedding = self._embed(doc)

        self.collection.add(
            documents=[doc],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[f"{user_id}_{self.collection.count()+1}"]
        )

    def retrieve_memories(self, user_id: str, query: str, top_k: int = 3) -> List[str]:
        embedding = self._embed(query)

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"user_id": user_id}
        )

        return results.get("documents", [[]])[0]

    def get_last_order_for_user(self, user_id: str) -> str | None:

        results = self.collection.query(
            query_texts=["pedido"],
            n_results=5,
            where={"user_id": user_id, "tipo": "pedido"}
        )

        docs = results.get("documents", [[]])[0]
        if not docs:
            return None

        for doc in reversed(docs):
            match = re.search(r"#(\d{5,10})", doc)
            if match:
                return match.group(1)

        return None
