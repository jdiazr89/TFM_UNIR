# Configuración central del proyecto.
# Pydantic Settings permite sobreescribir valores desde variables de entorno.
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Nombre descriptivo de la aplicación.
    app_name: str = "Asistente Conversacional con Memoria Vectorial"
    # Modelo de Ollama que se usará para generar respuestas.
    model_name: str = "llama3.1"
    # Carpeta local de persistencia de ChromaDB.
    chroma_dir: str = "vector_memory"
    # URL base del servidor Ollama.
    llm_base_url: str = "http://localhost:11434"
    # Timeout máximo por request al LLM.
    llm_timeout_seconds: int = 60
    # Número máximo de memorias inyectadas al prompt.
    max_memories: int = 2
    # Tamaño máximo de cada memoria enviada al prompt.
    max_memory_chars: int = 280
    # Modelo de embeddings para recuperación semántica.
    embedding_model_name: str = "all-MiniLM-L6-v2"

    class Config:
        # Archivo opcional para variables de entorno locales.
        env_file = ".env"

# Instancia global compartida por todo el backend.
settings = Settings()
