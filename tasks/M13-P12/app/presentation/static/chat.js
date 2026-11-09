const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const send = document.getElementById("send");
const record = document.getElementById("record");
const attach = document.getElementById("attach");
const imagePicker = document.getElementById("image-file");
const messages = document.getElementById("messages");
const status = document.getElementById("status");
const audioDraft = document.getElementById("audio-draft");
const imageDraft = document.getElementById("image-draft");
const audioPreview = document.getElementById("audio-preview");
const imagePreview = document.getElementById("image-preview");
const removeAudio = document.getElementById("remove-audio");
const removeImage = document.getElementById("remove-image");
let audioFile = null;
let imageFile = null;
let recorder = null;
let recordingTimer = null;

function setBusy(busy) {
  for (const control of [input, send, record, attach, imagePicker, removeAudio, removeImage]) {
    control.disabled = busy;
  }
}

function clearAudio() {
  audioPreview.pause();
  if (audioFile) URL.revokeObjectURL(audioPreview.src);
  audioPreview.removeAttribute("src");
  audioFile = null;
  audioDraft.hidden = true;
}

function clearImage() {
  if (imageFile) URL.revokeObjectURL(imagePreview.src);
  imagePreview.removeAttribute("src");
  imageFile = null;
  imageDraft.hidden = true;
  imagePicker.value = "";
}

removeAudio.addEventListener("click", () => { clearAudio(); status.textContent = ""; });
removeImage.addEventListener("click", () => { clearImage(); status.textContent = ""; });
attach.addEventListener("click", () => imagePicker.click());
imagePicker.addEventListener("change", () => {
  const file = imagePicker.files[0];
  if (!file) return;
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type) || file.size > 5 * 1024 * 1024) {
    status.textContent = "Elige una imagen PNG, JPEG o WebP de hasta 5 MB.";
    imagePicker.value = "";
    return;
  }
  clearImage();
  imageFile = file;
  imagePreview.src = URL.createObjectURL(file);
  imageDraft.hidden = false;
  status.textContent = "Imagen preparada. Pulsa Enviar cuando quieras enviarla.";
});

function stopRecording() {
  if (recorder?.state === "recording") {
    record.disabled = true;
    recorder.stop();
  }
}

record.addEventListener("click", async () => {
  if (recorder?.state === "recording") {
    stopRecording();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    status.textContent = "Este navegador no permite grabar aquí. Abre el chat en Chrome con localhost o HTTPS.";
    return;
  }
  record.disabled = true;
  send.disabled = true;
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mimeType = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"]
      .find((type) => MediaRecorder.isTypeSupported(type));
    recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    const parts = [];
    let failed = false;
    recorder.ondataavailable = (event) => {
      if (event.data.size) parts.push(event.data);
    };
    recorder.onerror = () => {
      failed = true;
      status.textContent = "No se pudo completar la grabación. Vuelve a intentarlo.";
    };
    recorder.onstop = () => {
      clearTimeout(recordingTimer);
      stream.getTracks().forEach((track) => track.stop());
      const type = recorder.mimeType;
      const blob = new Blob(parts, { type });
      if (!failed && blob.size) {
        clearAudio();
        const extension = type.includes("mp4") ? "m4a" : type.includes("ogg") ? "ogg" : "webm";
        audioFile = new File([blob], `grabacion.${extension}`, { type });
        audioPreview.src = URL.createObjectURL(audioFile);
        audioDraft.hidden = false;
        status.textContent = "Audio preparado. Escúchalo y pulsa Enviar cuando quieras enviarlo.";
      } else if (!failed) {
        status.textContent = "No se ha grabado audio. Vuelve a intentarlo.";
      }
      recorder = null;
      record.textContent = "Grabar";
      record.setAttribute("aria-pressed", "false");
      setBusy(false);
    };
    recorder.start();
    recordingTimer = setTimeout(stopRecording, 30000);
    record.textContent = "Detener";
    record.setAttribute("aria-pressed", "true");
    record.disabled = false;
    status.textContent = "Grabando… Pulsa Detener al terminar (máximo 30 segundos).";
  } catch {
    stream?.getTracks().forEach((track) => track.stop());
    recorder = null;
    setBusy(false);
    status.textContent = "No se pudo acceder al micrófono. Revisa el permiso del navegador y vuelve a intentarlo.";
  }
});

function addMessage(author, message, kind) {
  document.getElementById("empty")?.remove();
  const bubble = document.createElement("div");
  bubble.className = `message ${kind}`;
  const label = document.createElement("strong");
  label.textContent = author;
  const content = document.createElement("p");
  content.textContent = message.text;
  bubble.append(label, content);
  if (message.image_path) {
    const image = document.createElement("img");
    image.src = message.image_path;
    image.alt = "Imagen adjunta";
    bubble.append(image);
  }
  if (message.audio_path) {
    const audio = document.createElement("audio");
    audio.src = message.audio_path;
    audio.controls = true;
    audio.setAttribute("aria-label", "Audio adjunto");
    bubble.append(audio);
  }
  messages.append(bubble);
  messages.scrollTop = messages.scrollHeight;
}

async function loadHistory() {
  setBusy(true);
  status.textContent = "Cargando conversación…";
  try {
    const response = await fetch("/chat");
    if (!response.ok) throw new Error("Error al cargar el historial");
    for (const message of await response.json()) {
      addMessage(message.role === "user" ? "Tú" : "Asistente", message, message.role);
    }
    status.textContent = "";
    setBusy(false);
    input.focus();
  } catch {
    status.textContent = "No se pudo cargar la conversación. Recarga la página para volver a intentarlo.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (send.disabled || (!message && !audioFile && !imageFile)) return;
  const data = new FormData();
  data.append("message", message);
  if (audioFile) data.append("audio", audioFile);
  if (imageFile) data.append("image", imageFile);
  setBusy(true);
  status.textContent = "Esperando respuesta…";
  try {
    const response = await fetch("/chat", { method: "POST", body: data });
    if (!response.ok) throw new Error("Error al enviar el mensaje");
    addMessage("Tú", {
      text: message,
      audio_path: audioFile ? URL.createObjectURL(audioFile) : null,
      image_path: imageFile ? URL.createObjectURL(imageFile) : null,
    }, "user");
    addMessage("Asistente", { text: await response.text() }, "assistant");
    input.value = "";
    clearAudio();
    clearImage();
    status.textContent = "";
  } catch {
    status.textContent = "No se pudo enviar. El mensaje y los adjuntos siguen preparados para volver a intentarlo.";
  } finally {
    setBusy(false);
    input.focus();
  }
});

window.addEventListener("pagehide", () => {
  recorder?.stream.getTracks().forEach((track) => track.stop());
});

loadHistory();
