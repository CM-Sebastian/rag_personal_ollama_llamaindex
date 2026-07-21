import os
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
#Archivos necesarios para IA
from src.rag import PersonalRAG
#Pydantic para validar type hints
from pydantic import BaseModel


class Entradas(BaseModel):
    texto: str



#Obtener el path aboluto
current_dir = os.path.dirname(os.path.abspath(__file__))

static_path = os.path.join(current_dir, "static")
templates_path = os.path.join(current_dir, "templates")



#Desde aqui la logica con FastApi
app = FastAPI()

#Se suben al entorno local los archivos del front 

# 1. Montar archivos directorio de archivos estaticos (CSS, JS, Images)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# 2. Set up the templates directory (HTML)
templates = Jinja2Templates(directory=templates_path)


# Initial page load
@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request, "title": "My RAG App", "message": "Welcome!"},
    )


#Parte IA


@app.post("/chat-input")
def recibirMensaje(request: Entradas):

    entradaChat = request.texto
    #Falta meter rol aqui
    PersonalRAG.ask(request.texto,role=role)
    



"""
# Endpoint that returns the NEW element dynamically
@app.get("/get-element", response_class=HTMLResponse)
def get_element():
    # This raw HTML string will be injected without a page reload
    return "<p style='color: green;'>✅ This element came directly from Python!</p>"
"""