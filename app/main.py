from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.services.config.config_loader import config

from app.api.endpoints.document_loader import document_loader
from app.api.endpoints.chat import ask_question

from app.core.security import get_api_key

# Cargar variables de entorno
import os
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = FastAPI(
    title="IA API",
    description="API for AI Services",
    version="1.0.0",
    dependencies=[Depends(get_api_key)]  # Añadir dependencia a nivel de aplicación
)

allowed_origins_str = config['cors']['allowed_origins']
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP.
    allow_headers=["*"],  # Permitir todos los encabezados.
)

# Registrar routers
app.include_router(document_loader.router)
app.include_router(ask_question.router)

@app.get("/")
async def root():
    
    return {"message": "Welcome to IA API"}