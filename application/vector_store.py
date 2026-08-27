"""
Configuración del Vector Store (Qdrant). FUENTE ÚNICA del par (embedding, colección).

La ingesta (RAG-Clasico-con-Qdrant/rag.py) y la consulta
(tools/Base_de_conocimiento.py) importan de acá. El modelo de embeddings y el
nombre de la colección NO se escriben en ningún otro archivo.

Por qué importa: si la ingesta indexa con un modelo y la consulta busca con otro,
la búsqueda devuelve resultados vacíos o irrelevantes SIN lanzar ningún error.
El agente responde "no encontré información" sobre documentos que sí están
indexados, y no hay traza que seguir.

Requeridas en .env: QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY
Opcional: QDRANT_COLLECTION (default: tenant_id_alpha_state)

Autor: Ing. Kevin Inofuente Colque - DataPath
"""

import os

from dotenv import load_dotenv, find_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

load_dotenv(find_dotenv())

# ============================================
# CONFIGURACIÓN
# ============================================
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Convención multi-tenant: prefijo tenant_id_ (guiones bajos en Qdrant)
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "tenant_id_alpha_state")

# Un solo modelo para todo el proyecto. Cambiarlo obliga a REINDEXAR: la
# dimensión del vector es parte de la definición de la colección.
MODELO_EMBEDDING = "text-embedding-3-small"
EMBEDDING_DIM = 1536  # dimensión de text-embedding-3-small

if not QDRANT_URL:
    raise ValueError("❌ Falta QDRANT_URL en .env")


# ============================================
# FUNCIONES PÚBLICAS
# ============================================
def get_embedding_model() -> OpenAIEmbeddings:
    """Modelo de embeddings. El mismo para ingestar y para consultar.

    .strip() en la API key: el secreto en Secret Manager llega con un salto de
    línea al final y httpx rechaza el header ("Illegal header value ...\\n").
    """
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    return OpenAIEmbeddings(model=MODELO_EMBEDDING, api_key=api_key)


def get_client() -> QdrantClient:
    """Cliente del Qdrant del VPS.

    port=None es obligatorio: sin eso qdrant-client le agrega :6333 a la URL por
    su cuenta y la conexión muere con "Connection refused", porque el proxy del
    VPS (EasyPanel) publica Qdrant en el 443 de https, no en el 6333.
    """
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, port=None)


def ensure_collection(client: QdrantClient) -> None:
    """Crea la colección vacía si aún no existe.

    Sin esto, QdrantVectorStore valida la colección al instanciarse y, si la
    ingesta (rag.py) nunca corrió contra este Qdrant, lanza 404 y tumba el
    arranque del contenedor. Con la colección creada el servicio levanta; la
    tool de RAG simplemente no devuelve resultados hasta que se indexe.
    """
    if client.collection_exists(COLLECTION_NAME):
        return
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qmodels.VectorParams(
            size=EMBEDDING_DIM,
            distance=qmodels.Distance.COSINE,
        ),
    )


def get_vectorstore() -> QdrantVectorStore:
    """Vector store listo para consultar la colección del tenant."""
    client = get_client()
    ensure_collection(client)
    # validate_collection_config=False: ensure_collection ya garantizó que la
    # colección existe. La validación de langchain llama a OpenAI para medir la
    # dimensión del vector, y no queremos que el arranque del contenedor dependa
    # de una llamada de red a OpenAI.
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=get_embedding_model(),
        validate_collection_config=False,
    )
