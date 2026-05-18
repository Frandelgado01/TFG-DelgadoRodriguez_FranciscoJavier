"""
main.py — Servidor principal del Asistente RAG Vitivinícola
============================================================
Implementa los endpoints definidos en /api-spec/openapi.yaml siguiendo
la metodología Spec-Driven Development (SDD).

Endpoints implementados:
  - POST /ask              → Consulta RAG real (ChromaDB + Groq/Llama 3)
  - POST /documents/ingest → Ingesta real de PDFs normativos en ChromaDB

Dependencias (instalar con pip):
  pip install pypdf langchain-community langchain-huggingface
              sentence-transformers chromadb langchain-groq python-dotenv

Variables de entorno requeridas (archivo /backend/.env):
  GROQ_API_KEY=<tu_clave_groq>

Autor: TFG - Delgado Rodríguez, Francisco Javier
"""

import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# LangChain — carga de PDFs
from langchain_community.document_loaders import PyPDFLoader

# LangChain — división de texto
from langchain_text_splitters import RecursiveCharacterTextSplitter

# LangChain — embeddings locales (HuggingFace, sin API key)
from langchain_huggingface import HuggingFaceEmbeddings

# LangChain — base de datos vectorial ChromaDB
from langchain_community.vectorstores import Chroma

# LangChain — LLM Groq (Llama 3)
from langchain_groq import ChatGroq

# LangChain — LCEL (LangChain Expression Language)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever

# ---------------------------------------------------------------------------
# Carga de variables de entorno (.env)
# ---------------------------------------------------------------------------
# Se busca el .env en el directorio del propio fichero (backend/.env)
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuración de rutas y parámetros RAG
# ---------------------------------------------------------------------------

# Directorio raíz del backend (mismo directorio que este fichero)
BACKEND_DIR: Path = Path(__file__).parent

# Carpeta temporal para PDFs recibidos (se crea si no existe)
TEMP_DIR: Path = BACKEND_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Directorio de persistencia de ChromaDB
CHROMA_DB_DIR: Path = BACKEND_DIR / "chroma_db"
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# Parámetros del text splitter
CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 200

# Nombre de la colección dentro de ChromaDB
CHROMA_COLLECTION: str = "normativas_vitivinicolas"

# Modelo de embeddings local (descargado automáticamente la 1.ª vez, ~90 MB)
EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

# Modelo LLM de Groq — se puede cambiar por otro disponible en la plataforma
GROQ_MODEL: str = "llama-3.1-8b-instant"

# Número de fragmentos a recuperar de ChromaDB por consulta
TOP_K: int = 4

# Prompt del sistema para el asistente RAG
_SYSTEM_PROMPT: str = (
    "Eres un asistente experto en normativas vitivinícolas españolas y europeas, "
    "así como en el Cuaderno Digital de Explotación Agrícola (CUE). "
    "Tu función es responder de forma precisa, clara y en español, "
    "basándote ÚNICAMENTE en los fragmentos de documentos oficiales que se te proporcionan. "
    "Si la información necesaria para responder no está en el contexto proporcionado, "
    "indícalo explícitamente y NO inventes datos. "
    "Cita siempre la fuente documental cuando sea posible.\n\n"
    "Contexto recuperado de la base normativa:\n{context}"
)


# ---------------------------------------------------------------------------
# Inicialización de componentes pesados (una sola vez al arrancar)
# ---------------------------------------------------------------------------

def _load_embeddings() -> HuggingFaceEmbeddings:
    """Carga el modelo de embeddings local desde HuggingFace Hub."""
    logger.info("Cargando modelo de embeddings '%s'…", EMBEDDINGS_MODEL)
    return HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)


def _build_rag_components() -> tuple[VectorStoreRetriever, Runnable]:
    """
    Construye y devuelve los dos componentes del pipeline RAG usando
    exclusivamente LCEL (LangChain Expression Language).
    No importa nada de ``langchain.chains`` (eliminado en LangChain ≥ 1.0).

    Returns:
        Tupla ``(retriever, generation_chain)`` donde:
        - ``retriever``: busca en ChromaDB y devuelve ``List[Document]``.
        - ``generation_chain``: cadena LCEL ``prompt | llm | StrOutputParser``
          que acepta ``{"context": str, "input": str}`` y retorna ``str``.

    Raises:
        RuntimeError: Si ``GROQ_API_KEY`` no está definida en el entorno.
    """
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError(
            "La variable de entorno GROQ_API_KEY no está definida. "
            "Añádela al archivo backend/.env."
        )

    # 1. Conectar a ChromaDB existente como retriever (solo lectura)
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=_embeddings,
        persist_directory=str(CHROMA_DB_DIR),
    )
    retriever: VectorStoreRetriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )
    logger.info("Retriever ChromaDB listo (k=%d, colección='%s').", TOP_K, CHROMA_COLLECTION)

    # 2. Instanciar el LLM de Groq
    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=groq_api_key,
        temperature=0.1,   # respuestas deterministas y factuales
        max_tokens=1024,
    )
    logger.info("LLM Groq instanciado (modelo='%s').", GROQ_MODEL)

    # 3. Prompt de sistema — {context} e {input} se sustituyen en el handler
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    # 4. Cadena de generación pura LCEL: prompt | llm | parser
    #    Acepta {"context": str, "input": str} → devuelve str
    generation_chain: Runnable = prompt | llm | StrOutputParser()

    logger.info("Componentes RAG (LCEL) ensamblados correctamente.")
    return retriever, generation_chain


# Instancias globales — inicializadas al arrancar el servidor
_embeddings: HuggingFaceEmbeddings = _load_embeddings()
_retriever: VectorStoreRetriever
_generation_chain: Runnable
_retriever, _generation_chain = _build_rag_components()


# ---------------------------------------------------------------------------
# Modelos Pydantic (Request / Response)
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    """Cuerpo de la petición para el endpoint /ask."""

    question: str = Field(
        ...,
        min_length=1,
        description="Pregunta en lenguaje natural formulada por el viticultor.",
        examples=["¿Qué requisitos tiene el Cuaderno Digital (CUE) para viñedos ecológicos?"],
    )


class AskResponse(BaseModel):
    """Respuesta del asistente RAG para el endpoint /ask."""

    answer: str = Field(
        ...,
        description="Respuesta generada por el LLM con contexto recuperado de la base vectorial.",
        examples=["Según el RD 1048/2022, las explotaciones ecológicas deben..."],
    )
    sources: List[str] = Field(
        ...,
        description="Lista de referencias documentales utilizadas para generar la respuesta.",
        examples=[["BOE-A-2022-23054, pág 12", "RD 1048/2022, Art. 5"]],
    )


class IngestResponse(BaseModel):
    """Respuesta del endpoint /documents/ingest tras procesar un PDF."""

    message: str = Field(
        ...,
        description="Mensaje de confirmación sobre el procesamiento del documento.",
        examples=["Documento 'normativa_eco.pdf' procesado e indexado correctamente."],
    )
    filename: str = Field(
        ...,
        description="Nombre del archivo recibido y procesado.",
        examples=["normativa_eco.pdf"],
    )
    chunks_indexed: int = Field(
        ...,
        description="Número de fragmentos (chunks) generados e indexados en la base vectorial.",
        examples=[42],
    )


# ---------------------------------------------------------------------------
# Inicialización de la aplicación FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="API Asistente RAG Vitivinícola",
    description=(
        "API para la gestión del asistente conversacional basado en normativas "
        "del sector vitivinícola y sostenibilidad. "
        "Definida según el contrato OpenAPI en /api-spec/openapi.yaml."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc
)

# ---------------------------------------------------------------------------
# Configuración CORS
# ---------------------------------------------------------------------------
# Permite peticiones desde el frontend local de Vite (puerto 5173).
# En producción sustituir los orígenes por el dominio real del frontend.

ALLOWED_ORIGINS: List[str] = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",  # Alias local
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, OPTIONS…
    allow_headers=["*"],   # Authorization, Content-Type…
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    summary="Enviar una pregunta al asistente",
    description=(
        "Recibe una pregunta del viticultor y devuelve una respuesta generada "
        "por el LLM (Groq/Llama 3) junto con las fuentes normativas recuperadas "
        "de la base vectorial ChromaDB local (pipeline RAG real)."
    ),
    tags=["RAG"],
)
async def ask(request: AskRequest) -> AskResponse:
    """
    Ejecuta el pipeline RAG completo usando LCEL puro (sin langchain.chains).

    Pipeline de dos pasos explícitos:
      1. ``_retriever.ainvoke(question)``  →  List[Document] con metadatos.
      2. Concatenación del contenido de los docs como contexto de texto plano.
      3. ``_generation_chain.ainvoke({context, input})``  →  str con la respuesta.
      4. Extracción de fuentes deduplicadas desde los metadatos de los docs.

    Args:
        request: Objeto ``AskRequest`` con el campo ``question``.

    Returns:
        ``AskResponse`` con ``answer`` (texto del LLM) y ``sources``
        (lista deduplicada de referencias documentales con número de página).

    Raises:
        HTTPException(503): Si los componentes RAG no están disponibles.
        HTTPException(500): Si ocurre un error durante la recuperación o inferencia.
    """
    logger.info("Consulta RAG recibida: '%s'", request.question)

    # ── Paso 1: Recuperar documentos relevantes de ChromaDB ──────────────────
    try:
        docs = await _retriever.ainvoke(request.question)
    except Exception as exc:
        logger.error("Error en la recuperación ChromaDB: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar la base de datos vectorial: {exc}",
        ) from exc

    logger.info("Documentos recuperados de ChromaDB: %d", len(docs))

    # ── Paso 2: Formatear el contexto como texto plano ───────────────────────
    # Cada Document contiene .page_content (texto) y .metadata (source, page)
    context: str = "\n\n".join(doc.page_content for doc in docs)

    # ── Paso 3: Generar respuesta con el LLM (LCEL: prompt | llm | parser) ───
    try:
        answer: str = await _generation_chain.ainvoke(
            {"context": context, "input": request.question}
        )
    except Exception as exc:
        logger.error("Error durante la inferencia con Groq: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar la respuesta con el modelo de lenguaje: {exc}",
        ) from exc

    # ── Paso 4: Extraer fuentes únicas de los metadatos ─────────────────────
    # PyPDFLoader añade: metadata["source"] = ruta del PDF, metadata["page"] = nº (0-indexed)
    sources: List[str] = []
    seen: set[str] = set()
    for doc in docs:
        meta = doc.metadata
        source_file: str = Path(meta.get("source", "Fuente desconocida")).name
        page_num: int | None = meta.get("page")  # 0-indexed → mostramos +1
        ref: str = (
            f"{source_file}, pág. {page_num + 1}"
            if page_num is not None
            else source_file
        )
        if ref not in seen:
            seen.add(ref)
            sources.append(ref)

    logger.info(
        "Respuesta generada. Fuentes consultadas (%d): %s", len(sources), sources
    )
    return AskResponse(answer=answer, sources=sources)


@app.post(
    "/documents/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Subir nueva normativa al sistema",
    description=(
        "Endpoint para procesar PDFs (BOE, PAC) y convertirlos en embeddings "
        "en la base de datos vectorial ChromaDB local. "
        "Utiliza PyPDFLoader + RecursiveCharacterTextSplitter + "
        "HuggingFace all-MiniLM-L6-v2 (sin API key, 100% local)."
    ),
    tags=["Documentos"],
)
async def ingest_document(
    file: UploadFile = File(..., description="Documento PDF con la normativa a indexar."),
) -> IngestResponse:
    """
    Recibe un fichero PDF, lo procesa y lo almacena en la base vectorial.

    Pipeline real:
      1. Valida el tipo MIME del fichero.
      2. Persiste el PDF en ``/backend/temp`` con nombre único (UUID).
      3. Extrae el texto con ``PyPDFLoader``.
      4. Divide el texto con ``RecursiveCharacterTextSplitter``.
      5. Genera embeddings con ``HuggingFaceEmbeddings`` (all-MiniLM-L6-v2).
      6. Almacena los chunks en ChromaDB (``/backend/chroma_db``).
      7. Elimina el fichero temporal.

    Args:
        file: Fichero PDF subido mediante ``multipart/form-data``.

    Returns:
        ``IngestResponse`` con mensaje de confirmación, nombre del fichero
        y número real de chunks indexados.

    Raises:
        HTTPException(400): Si el fichero no es un PDF válido o su contenido
                            está vacío / no se pudo extraer texto.
        HTTPException(500): Si ocurre un error inesperado durante el pipeline.
    """
    # ------------------------------------------------------------------
    # 1. Validación del tipo MIME
    # ------------------------------------------------------------------
    VALID_MIME_TYPES: tuple[str, ...] = (
        "application/pdf",
        "application/octet-stream",  # algunos clientes HTTP envían este tipo
    )
    if file.content_type not in VALID_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Tipo de fichero no soportado: '{file.content_type}'. "
                "Solo se admiten documentos PDF."
            ),
        )

    original_filename: str = file.filename or "documento.pdf"

    # ------------------------------------------------------------------
    # 2. Guardar PDF en carpeta temporal con nombre único (evita colisiones)
    # ------------------------------------------------------------------
    unique_name: str = f"{uuid.uuid4().hex}_{original_filename}"
    temp_path: Path = TEMP_DIR / unique_name

    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info("PDF guardado temporalmente en: %s", temp_path)

        # ----------------------------------------------------------------
        # 3. Extraer texto con PyPDFLoader
        # ----------------------------------------------------------------
        try:
            loader = PyPDFLoader(str(temp_path))
            pages = loader.load()  # lista de Document (uno por página)
        except Exception as exc:
            logger.error("Error al leer el PDF '%s': %s", original_filename, exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No se pudo extraer texto del fichero '{original_filename}'. "
                    "Asegúrate de que es un PDF válido y no está protegido con contraseña."
                ),
            ) from exc

        if not pages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El PDF '{original_filename}' no contiene páginas legibles.",
            )

        logger.info("Páginas extraídas de '%s': %d", original_filename, len(pages))

        # ----------------------------------------------------------------
        # 4. Dividir el texto en chunks
        # ----------------------------------------------------------------
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        chunks = splitter.split_documents(pages)
        logger.info("Chunks generados para '%s': %d", original_filename, len(chunks))

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"El PDF '{original_filename}' no generó fragmentos procesables. "
                    "El documento podría estar basado en imágenes (PDF escaneado)."
                ),
            )

        # ----------------------------------------------------------------
        # 5 & 6. Generar embeddings y persistir en ChromaDB
        # ----------------------------------------------------------------
        try:
            vectorstore = Chroma(
                collection_name=CHROMA_COLLECTION,
                embedding_function=_embeddings,
                persist_directory=str(CHROMA_DB_DIR),
            )
            vectorstore.add_documents(chunks)
            logger.info(
                "Indexados %d chunks de '%s' en ChromaDB (%s).",
                len(chunks),
                original_filename,
                CHROMA_DB_DIR,
            )
        except Exception as exc:
            logger.error("Error al indexar en ChromaDB: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al almacenar los embeddings en la base vectorial.",
            ) from exc

    finally:
        # ----------------------------------------------------------------
        # 7. Eliminar el fichero temporal (siempre, incluso si hay error)
        # ----------------------------------------------------------------
        if temp_path.exists():
            temp_path.unlink()
            logger.info("Fichero temporal eliminado: %s", temp_path)

    return IngestResponse(
        message=f"Documento '{original_filename}' procesado e indexado correctamente.",
        filename=original_filename,
        chunks_indexed=len(chunks),
    )


# ---------------------------------------------------------------------------
# Health-check (endpoint auxiliar, no definido en el spec)
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Comprobación de estado del servidor",
    tags=["Sistema"],
    include_in_schema=True,
)
async def health_check() -> dict:
    """Devuelve el estado del servidor. Útil para sondeos de CI/CD y monitorización."""
    return {"status": "ok", "version": app.version}
