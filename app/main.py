from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from app.router_chat import router as chat_router


app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas SIN prefix adicional (el prefix ya está en router_chat.py)
app.include_router(chat_router)

# 🔥 Warm-up automático del modelo
@app.on_event("startup")
async def warmup_model():
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3.1", "prompt": "warmup"},
            timeout=1
        )
    except:
        pass  # No bloquear si Ollama tarda
