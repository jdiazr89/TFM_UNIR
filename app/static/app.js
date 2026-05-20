const API_BASE = "http://127.0.0.1:8000/api";

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// Agregar mensaje al chat
function appendMessage(sender, text, cssClass) {
    const msg = document.createElement("div");
    msg.classList.add(cssClass);

    msg.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Eliminar mensajes temporales ("Escribiendo...")
function removeTempMessages() {
    document.querySelectorAll(".bot-temp").forEach(el => el.remove());
}

// Enviar mensaje
async function sendMessage(customText = null) {
    const message = customText ?? userInput.value.trim();
    if (!message) return;

    appendMessage("Tú", message, "user-message");
    userInput.value = "";

    // Mostrar indicador "Escribiendo..."
    appendMessage("Asistente", "Escribiendo...", "bot-temp");

    try {
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
        console.error(error);
        removeTempMessages();
        appendMessage("Sistema", "Error al conectar con el servidor.", "bot-message");
    }
}

// Eventos
sendBtn.addEventListener("click", () => sendMessage());
userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

// Acciones rápidas
document.querySelectorAll(".quick-action").forEach(btn => {
    btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-text");
        sendMessage(text);
    });
});

// Mensaje inicial automático
appendMessage(
    "Asistente",
    "Hola, soy Compita, tu asistente virtual de atención al cliente. ¿En qué puedo ayudarte hoy?",
    "bot-message"
);
