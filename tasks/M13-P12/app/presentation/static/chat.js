const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const send = document.getElementById("send");
const messages = document.getElementById("messages");
const status = document.getElementById("status");

async function loadHistory() {
  input.disabled = true;
  send.disabled = true;
  status.textContent = "Cargando conversación…";
  try {
    const response = await fetch("/chat");
    if (!response.ok) throw new Error("Error al cargar el historial");
    for (const message of await response.json()) {
      addMessage(message.role === "user" ? "Tú" : "Asistente", message.text, message.role);
    }
    status.textContent = "";
  } catch {
    status.textContent = "No se pudo cargar la conversación. Recarga la página para volver a intentarlo.";
    return;
  }
  input.disabled = false;
  send.disabled = false;
  input.focus();
}

function addMessage(author, text, kind) {
  document.getElementById("empty")?.remove();
  const bubble = document.createElement("div");
  bubble.className = `message ${kind}`;
  const label = document.createElement("strong");
  label.textContent = author;
  const content = document.createElement("p");
  content.textContent = text;
  bubble.append(label, content);
  messages.append(bubble);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || send.disabled) return;

  addMessage("Tú", message, "user");
  input.value = "";
  input.disabled = true;
  send.disabled = true;
  status.textContent = "Esperando respuesta…";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) throw new Error("Error al enviar el mensaje");
    addMessage("Asistente", await response.text(), "assistant");
    status.textContent = "";
  } catch {
    status.textContent = "No se pudo obtener respuesta. Comprueba que el servidor esté disponible y vuelve a enviar el mensaje.";
    input.value = message;
  } finally {
    input.disabled = false;
    send.disabled = false;
    input.focus();
  }
});

loadHistory();
