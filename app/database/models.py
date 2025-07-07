from sqlalchemy import Column, Integer, String
from .database import Base

class Clientes(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255))

# Tabla para embeddings por cliente
class EmbeddingsClientes(Base):
    __tablename__ = "embeddings_clientes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer)
    embedding = Column(String(255))  # Puedes ajustar el tipo de dato según tus necesidades