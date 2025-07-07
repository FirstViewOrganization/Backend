import os
from typing import List
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
# Importaciones para la base de datos
from app.database.database import SessionLocal
from app.database.models import EmbeddingsClientes

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY no se encontró en .env")

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

# Función para guardar la colección en la base de datos
def save_collection_to_db(collection_name, cliente_id=None):
    """Guarda la información de la colección en la tabla embeddings_clientes"""
    try:
        # Crear una sesión de base de datos
        db = SessionLocal()
        
        # Crear un nuevo registro
        new_embedding = EmbeddingsClientes(
            cliente_id=cliente_id,  # Si no se proporciona, será None
            embedding=collection_name
        )
        
        # Añadir y guardar en la base de datos
        db.add(new_embedding)
        db.commit()
        db.refresh(new_embedding)
        
        print(f"Colección '{collection_name}' guardada en la base de datos con ID: {new_embedding.id}")
        return new_embedding.id
    except Exception as e:
        print(f"Error al guardar la colección en la base de datos: {e}")
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()

def process_documents(documents_dir: str):
    print("Procesando documentos...", documents_dir)
    """
    Procesa los documentos en un directorio y almacena los embeddings en Chroma.
    Cada carpeta dentro del directorio principal tendrá su propia colección.
    """
    try:
        # Verificar si el directorio existe
        if not os.path.exists(documents_dir):
            raise ValueError("El directorio no existe")
            
        # Obtener lista de carpetas en el directorio
        # Si no hay subcarpetas, usar el directorio principal como única colección
        subdirs = [f.path for f in os.scandir(documents_dir) if f.is_dir()]
        
        if not subdirs:  # Si no hay subcarpetas, procesar todo el directorio como una colección
            process_single_directory(documents_dir, p_collection)
            # Guardar la colección en la base de datos
            save_collection_to_db(p_collection)
        else:  # Procesar cada subcarpeta como una colección separada
            for subdir in subdirs:
                # Usar el nombre de la carpeta como nombre de la colección
                collection_name = os.path.basename(subdir)
                process_single_directory(subdir, collection_name)
                # Guardar la colección en la base de datos
                # Aquí podrías intentar extraer un cliente_id del nombre de la colección si sigue algún patrón
                # Por ejemplo, si las carpetas se llaman "cliente_1", "cliente_2", etc.
                cliente_id = None
                try:
                    # Intenta extraer un ID de cliente si el nombre sigue un patrón como "cliente_123"
                    if collection_name.startswith("cliente_"):
                        cliente_id = int(collection_name.split("_")[1])
                except (ValueError, IndexError):
                    pass  # Si no se puede extraer un ID, se usará None
                
                save_collection_to_db(collection_name, cliente_id)
                
        print("Documentos procesados y embeddings almacenados en Chroma y en la base de datos.")
    except Exception as e:
        print(f"Error al procesar documentos: {e}")
        raise

def process_single_directory(directory: str, collection_name: str):
    """
    Procesa los documentos en un único directorio y los almacena en una colección específica.
    """
    # Cargar documentos
    loader = DirectoryLoader(directory, glob="**/*")
    documents = loader.load()
    print(f"Documentos cargados de {directory}: {len(documents)}")
    
    if not documents:
        print(f"No se encontraron documentos en {directory}")
        return
    
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
        print(f"No se encontraron textos para procesar en {directory}.")
        return

    print(f"Procesando {len(texts)} fragmentos para la colección {collection_name}")
    
    # Crear y almacenar embeddings en Chroma
    vectorstore = Chroma.from_documents(
        texts, 
        embeddings, 
        persist_directory=CHROMA_DB_DIR, 
        collection_name=collection_name
    )
    
    vectorstore.persist()  # Guardar la base de datos en disco
