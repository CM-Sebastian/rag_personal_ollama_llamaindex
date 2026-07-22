// Chat frontend logic: robust handlers, role toggle, send/receive messages

const navMenu = document.getElementById("menu-div");
const divChatMensajes = document.getElementById("chatMensajes");
const strMensaje = document.getElementById("textoMensaje");
const btnChatEnviar = document.getElementById("botonEnviar");
const rolCuadro = document.getElementById("rol-div");
const loginPanel = document.getElementById("login-panel");
const loginUsername = document.getElementById("loginUsername");
const loginPassword = document.getElementById("loginPassword");
const loginButton = document.getElementById("loginButton");
const loginError = document.getElementById("loginError");
const chatWrapper = document.getElementById("chat-wrapper");
const logoutButton = document.getElementById("logoutButton");

let rol = "1"; // default role: coincide con el botón "Reclutador"
let authToken = null;
let isSending = false;
//Para almacenar el usuario actual
let usuarioActual = "cliente" //por default

function scrollToBottom() {
  divChatMensajes.scrollTop = divChatMensajes.scrollHeight;
}

function createBubble(text, kind) {
  const el = document.createElement('div');
  el.className = `mensaje ${kind === 'user' ? 'enviado' : 'recibido'}`;
  const p = document.createElement('p');
  p.innerText = text;
  el.appendChild(p);
  return el;
}

function createTypingBubble() {
  const el = document.createElement('div');
  el.className = 'mensaje recibido typing';
  el.innerHTML = '<p>...</p>';
  return el;
}

async function postToServer(text, role) {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  const resp = await fetch('/chat-input', {
    method: 'POST',
    headers,
    body: JSON.stringify({ texto: text, role: role, token: authToken })
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`Server error ${resp.status}: ${txt}`);
  }
  return resp.json();
}

async function sendMessage(text, roleValue, { showUserBubble = true } = {}) {
  // isSending es la guarda clave: el backend abre un QdrantClient en modo
  // local con lock exclusivo, así que NUNCA deben salir dos peticiones a la
  // vez (por eso el saludo automático de abajo también pasa por esta misma
  // función en vez de llamar a postToServer directamente).
  if (!text || isSending) return;
  isSending = true;
  btnChatEnviar.disabled = true;

  if (showUserBubble) {
    const userBubble = createBubble(text, 'user');
    divChatMensajes.appendChild(userBubble);
    scrollToBottom();
  }

  // Add typing indicator
  const typing = createTypingBubble();
  divChatMensajes.appendChild(typing);
  scrollToBottom();

  try {
    const data = await postToServer(text, roleValue);
    // remove typing bubble
    typing.remove();

    const answer = data.answer || 'No hay respuesta del servidor.';
    const aiBubble = createBubble(answer, 'ai');
    divChatMensajes.appendChild(aiBubble);

    // optionally show sources (small, dimmed)
    if (Array.isArray(data.sources) && data.sources.length && usuarioActual == "admin") {
      const meta = document.createElement('div');
      meta.style.fontSize = '0.8em';
      meta.style.opacity = '0.8';
      meta.style.marginTop = '6px';
      meta.innerText = data.sources.map(s => `${s.file_name} (score=${s.score})`).join(' | ');
      aiBubble.appendChild(meta);
    }

    scrollToBottom();
  } catch (err) {
    console.error('Error sending message', err);
    typing.remove();
    const errBubble = createBubble(`Error: ${err.message || 'no se pudo conectar con el servidor.'}`, 'ai');
    divChatMensajes.appendChild(errBubble);
    scrollToBottom();
  } finally {
    isSending = false;
    btnChatEnviar.disabled = false;
  }
}

// Robust nav menu handler (use closest to support inner elements)
navMenu.addEventListener('click', (e) => {
  const button = e.target.closest('button');
  if (!button) return;

  // toggle selected style
  const botones = navMenu.querySelectorAll('button');
  botones.forEach(b => b.classList.remove('seleccionado'));
  button.classList.add('seleccionado');

  if (button.id === 'NuevoChat') {
    // clear messages
    divChatMensajes.replaceChildren();
  } else if (button.id === 'CambiarRol') {
    // toggle role box visibility
    if (rolCuadro.classList.contains('oculto')) {
      rolCuadro.classList.remove('oculto');
    } else {
      rolCuadro.classList.add('oculto');
    }
  }
});

// Role selection handler (delegated)
rolCuadro.addEventListener('click', (e) => {
  const button = e.target.closest('button');
  if (!button) return;
  const botones = rolCuadro.querySelectorAll('button');
  botones.forEach(b => b.classList.remove('seleccionado'));
  button.classList.add('seleccionado');
  if (button.dataset && button.dataset.role) {
    rol = button.dataset.role;
  }
  // hide role box after selection
  rolCuadro.classList.add('oculto');
});

// Send on Enter (Shift+Enter for newline)
strMensaje.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    btnChatEnviar.click();
  }
});

btnChatEnviar.addEventListener('click', async () => {
  const text = strMensaje.value.trim();
  if (!text) {
    strMensaje.placeholder = 'Debes escribir algo primero...';
    return;
  }
  // clear input and send
  strMensaje.value = '';
  await sendMessage(text, rol);
});

loginButton.addEventListener('click', async () => {
  loginError.classList.add('oculto');
  const username = loginUsername.value.trim();
  const password = loginPassword.value.trim();
  if (!username || !password) {
    loginError.textContent = 'Usuario y contraseña son obligatorios.';
    loginError.classList.remove('oculto');
    return;
  }
  try {
    const resp = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!resp.ok) {
      const body = await resp.json();
      loginError.textContent = body.detail || 'Error de autenticación.';
      loginError.classList.remove('oculto');
      return;
    }
    const data = await resp.json();
    authToken = data.token;
    usuarioActual = data.username
    loginPanel.classList.add('oculto');
    chatWrapper.classList.remove('oculto');
    logoutButton.classList.remove('oculto');
    loginUsername.value = '';
    loginPassword.value = '';
    sendMessage('Hi', rol, { showUserBubble: false });
  } catch (err) {
    loginError.textContent = 'No se pudo conectar con el servidor.';
    loginError.classList.remove('oculto');
  }
});

logoutButton.addEventListener('click', () => {
  authToken = null;
  loginPanel.classList.remove('oculto');
  chatWrapper.classList.add('oculto');
  logoutButton.classList.add('oculto');
  divChatMensajes.replaceChildren();
});

window.addEventListener('load', () => {
  // Do not send greeting until login.
});
