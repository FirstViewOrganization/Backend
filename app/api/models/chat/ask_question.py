from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os

router = APIRouter()

embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), 
                              model="text-embedding-3-small" )

# Configurar el modelo
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Ruta donde se almacenaron los embeddings
CHROMA_DB_DIR = "./chroma_db"

p_collection = "embedding_general"

# Cargar vectorstore desde la base de datos persistida
vectorstore = Chroma(
    persist_directory=CHROMA_DB_DIR,
    embedding_function=embeddings
)

# Crear una cadena de QA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever()
)

# Modelo para la solicitud del usuario
class UserQuery(BaseModel):
    question: str


# Endpoint para responder preguntas
@router.post("/ask")
async def ask_question(query: UserQuery):
    try:
        print("Pregunta 2:", query.question)
        custom_prompt = "Por favor, tomate el tiempo para analizar el texto del embedding y responde de manera amable: "

        # Generar respuesta usando la cadena de QA con el prompt personalizado
        response = qa_chain.invoke(custom_prompt + query.question)
        # Generar respuesta usando la cadena de QA
        # response = qa_chain.invoke(query.question)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de prueba
@router.get("/")
async def read_root():
    return {"message": "Bienvenido al sistema de conocimiento de la empresa"}
