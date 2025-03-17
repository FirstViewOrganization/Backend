from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from app.api.document_loader import router as document_loader_router
from app.api.ask_question import router as ask_question_router

# Cargar variables de entorno
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Configurar OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP.
    allow_headers=["*"],  # Permitir todos los encabezados.
)

# Registrar routers
app.include_router(document_loader_router, prefix="/api")
app.include_router(ask_question_router, prefix="/api")

# Modelo para la solicitud del usuario
class UserQuery(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(query: UserQuery):
    try:
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": query.question},
        ],
        stream=False
        )
        # Construir la respuesta JSON
        answer = response.choices[0].message.content

        return JSONResponse(content={"success": True, "answer": answer}, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def read_root():
    return {"message": "Bienvenido al sistema de conocimiento de la empresa"}
