import os
from typing import List
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY no se encontró en .env")
else:
    print("API Key cargada correctamente")

p_collection = 'embedding_general'

# Configurar embeddings
embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"), model="text-embedding-3-small")

# Ruta donde se almacenarán los embeddings de Chroma
CHROMA_DB_DIR = "./chroma_db"

# Función para cargar PDFs
def load_pdf(file_path):
    with open(file_path, "rb") as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

# Función para cargar DOCX
def load_docx(file_path):
    doc = Document(file_path)
    text = ""
    for para in doc.paragraphs:
        text += para.text
    return text

# Función para cargar TXT
def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Función para detectar el tipo de archivo y cargar el contenido
def load_file(file_path):
    print(f"Cargando archivo: {file_path}")
    if file_path.endswith('.pdf'):
        return load_pdf(file_path)
    elif file_path.endswith('.docx'):
        return load_docx(file_path)
    elif file_path.endswith('.txt'):
        return load_txt(file_path)
    else:
        return None  # Agrega más formatos si es necesario

def process_documents(documents_dir: str):
    print("Procesando documentos...", documents_dir)
    """
    Procesa los documentos en un directorio y almacena los embeddings en Chroma.
    """
    try:
        # Verificar si el directorio existe
        if not os.path.exists(documents_dir):
            raise ValueError("El directorio no existe")

        # Cargar documentos
        # loader = DirectoryLoader(documents_dir, glob="**/*.{txt,pdf,docx}")  # Incluir otros tipos si es necesario
        loader = DirectoryLoader(documents_dir, glob="**/*")

        documents = loader.load()
        print(f"Documentos cargados: {documents}")

        # Procesar el contenido de los archivos
        for doc in documents:
            file_path = doc.metadata['source']
            doc.page_content = load_file(file_path)  # Cargar el contenido del archivo

        # Dividir documentos en fragmentos
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Tamaño de cada fragmento
            chunk_overlap=200  # Superposición entre fragmentos
        )
        texts = text_splitter.split_documents(documents)

        if not texts:
            raise ValueError("No se encontraron textos para procesar.")

        print(f"Texts: {texts}")  # Verificar si hay textos
        print(f"Embeddings: {embeddings}")  # Verificar si hay embeddings

        # Crear y almacenar embeddings en Chroma
        vectorstore = Chroma.from_documents(texts, embeddings, persist_directory=CHROMA_DB_DIR)
    

        vectorstore.persist()  # Guardar la base de datos en disco

        print("Documentos procesados y embeddings almacenados en Chroma.")
    except Exception as e:
        print(f"Error al procesar documentos: {e}")
        raise
