from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.document_services import process_documents

router = APIRouter()

@router.post("/load-documents")
async def load_documents(background_tasks: BackgroundTasks):
    """
    Endpoint para cargar documentos desde un directorio.
    """
    try:
        # Ruta del directorio que contiene los documentos
        documents_dir = "C:/Proyectos/Eve/backend/documents"  # Cambia esto por la ruta correcta

        # Ejecutar el procesamiento en segundo plano
        background_tasks.add_task(process_documents, documents_dir)

        return {"message": "Carga de documentos iniciada. Los documentos se están procesando en segundo plano."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))