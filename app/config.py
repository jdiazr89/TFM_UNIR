from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Asistente Conversacional con Memoria Vectorial"
    model_name: str = "llama3.1"
    chroma_dir: str = "vector_memory"

    class Config:
        env_file = ".env"

settings = Settings()
