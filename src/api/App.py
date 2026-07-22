import json
import logging
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.auth import AuthDB
from src.config import AppConfig
from src.rag import PersonalRAG
from src.roles import get_role

logger = logging.getLogger("rag_app")


class Entradas(BaseModel):
    texto: str
    role: str = "5"
    token: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Estado compartido de la app (se rellena en el lifespan)
rag_state: dict = {"rag": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # IMPORTANTE: PersonalRAG abre un QdrantClient en modo local (path=...),
    # que usa un lock exclusivo sobre la carpeta de la base de datos.
    # Si se crea una instancia nueva en cada request (como antes), dos
    # peticiones que se solapen (p. ej. el saludo automático del frontend
    # + un mensaje del usuario) chocan contra ese lock y el endpoint falla
    # con un error 500. Por eso se crea UNA sola vez aquí, al arrancar el
    # servidor, y se reutiliza para todas las peticiones.
    config = AppConfig()
    # create auth DB and seed sample static users if necessary
    auth_db = AuthDB(config.auth_db_path)
    auth_db.init_db()
    seed_path = Path(current_dir) / 'static' / 'users.json'
    if seed_path.exists():
        with open(seed_path, 'r', encoding='utf-8') as f:
            try:
                seed_users = json.load(f)
            except json.JSONDecodeError:
                seed_users = []
        for user in seed_users:
            try:
                auth_db.create_user(user['username'], user['password'], user.get('role', 'general'))
            except sqlite3.IntegrityError:
                # User already exists, silently skip (idempotent seed)
                pass
            except Exception:
                logger.exception("Error creando usuario de seed %s", user.get('username'))
    app.state.auth_db = auth_db
    try:
        rag_state['rag'] = PersonalRAG(config)
        logger.info('RAG inicializado correctamente.')
    except Exception:
        logger.exception('No se pudo inicializar el RAG al arrancar el servidor.')
        rag_state['rag'] = None
    yield
    if rag_state['rag'] is not None:
        rag_state['rag'].close()


#Obtener el path aboluto
current_dir = os.path.dirname(os.path.abspath(__file__))

static_path = os.path.join(current_dir, "static")
templates_path = os.path.join(current_dir, "templates")



#Desde aqui la logica con FastApi
app = FastAPI(lifespan=lifespan)

#Se suben al entorno local los archivos del front 

# 1. Montar archivos directorio de archivos estaticos (CSS, JS, Images)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 2. Configurar plantillas (HTML)
templates = Jinja2Templates(directory=templates_path)


# Initial page load
@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "title": "My RAG App", "message": "Welcome!"},
    )


@app.post("/login")
def login(request: LoginRequest):
    auth_db: AuthDB = app.state.auth_db
    user = auth_db.verify_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = str(uuid.uuid4())
    cache_path = Path(app.state.auth_db.db_path.parent) / 'session_tokens.json'
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
    else:
        sessions = {}
    sessions[token] = {
        'username': user['username'],
        'role': user['role']['key'],
        'created_at': datetime.utcnow().isoformat(),
    }
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(sessions, f)
    return {'token': token, 'username': user['username'], 'role': user['role']['key']}


def validate_token(token: str | None):
    if not token:
        return None
    cache_path = Path(app.state.auth_db.db_path.parent) / 'session_tokens.json'
    if not cache_path.exists():
        return None
    with open(cache_path, 'r', encoding='utf-8') as f:
        sessions = json.load(f)
    return sessions.get(token)


#Parte IA


@app.post("/chat-input")
def recibirMensaje(request: Request, entradas: Entradas):
    auth_header = request.headers.get('Authorization', '')
    auth_token = None
    if auth_header.startswith('Bearer '):
        auth_token = auth_header[len('Bearer '):].strip()
    if not auth_token:
        auth_token = entradas.token
    auth = validate_token(auth_token)
    if auth is None:
        raise HTTPException(status_code=401, detail="Token de sesión inválido o expirado.")
    rag = rag_state.get("rag")
    if rag is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "El motor RAG no está disponible. Revisa los logs del servidor: "
                "puede que falte ejecutar 'python -m src.cli ingest' o que Ollama "
                "no esté corriendo."
            ),
        )
    try:
        role_dict = get_role(entradas.role)
        result = rag.ask(entradas.texto, role_dict)
        return {
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "language": result.get("language"),
            "user": auth["username"],
            "role": auth["role"],
        }
    except Exception:
        logger.exception("Error procesando el mensaje en /chat-input")
        raise HTTPException(status_code=500, detail="Error interno procesando el mensaje.")

