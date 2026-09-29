// URL base del backend FastAPI.
const API_BASE = "http://127.0.0.1:8000/api";

// Referencias a elementos principales de la interfaz de chat.
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Agregar mensaje al chat
function appendMessage(sender, text, cssClass) {
    // Crea un contenedor por mensaje para mantener estilos separados por rol.
    const msg = document.createElement("div");
    msg.classList.add(cssClass);

    // Inserta autor + texto y ajusta scroll al final del historial.
    msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Eliminar mensajes temporales ("Escribiendo...")
function removeTempMessages() {
    // Elimina placeholders para no mezclar estados con mensajes definitivos.
    document.querySelectorAll(".bot-temp").forEach(el => el.remove());
}

// Enviar mensaje
async function sendMessage(customText = null) {
    // Permite enviar texto manual o usar accesos rápidos predefinidos.
    const message = customText ?? userInput.value.trim();
    if (!message) return;

    appendMessage("Tú", message, "user-message");
    userInput.value = "";

    // Mostrar indicador "Escribiendo..."
    appendMessage("Asistente", "Escribiendo...", "bot-temp");

    try {
        // Invoca endpoint /chat con user_id fijo de demo.
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: "usuario_demo",
                message: message
            })
        });

        const data = await response.json();
        removeTempMessages();

        if (!response.ok) {
            // Errores HTTP controlados por backend.
            const errorText = data.detail || "Ocurrió un error en el servidor.";
            appendMessage("Sistema", errorText, "bot-message");
            return;
        }

        appendMessage("Asistente", data.reply, "bot-message");

        // Indicador profesional de memoria
        if (data.used_memory && data.retrieved_memories.length > 0) {
            document.getElementById("memory-indicator").style.visibility = "visible";
        } else {
            document.getElementById("memory-indicator").style.visibility = "hidden";
        }

    } catch (error) {
        // Error de red/timeout al contactar el backend.
        console.error(error);
        removeTempMessages();
        appendMessage("Sistema", "Error al conectar con el servidor.", "bot-message");
    }
}

// Eventos de envío por botón o tecla Enter.
sendBtn.addEventListener("click", () => sendMessage());
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

// Botones rápidos para disparar intents frecuentes.
document.querySelectorAll(".quick-action").forEach(btn => {
    btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-text");
        sendMessage(text);
    });
});

// Mensaje inicial para contextualizar al usuario al abrir la interfaz.
appendMessage(
    "Asistente",
    "Hola, soy Compita, tu asistente virtual de atención al cliente. ¿En qué puedo ayudarte hoy?",
    "bot-message"
);
