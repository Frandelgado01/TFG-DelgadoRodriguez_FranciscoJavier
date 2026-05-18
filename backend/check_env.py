"""
check_env.py — Script de diagnóstico del entorno virtual Python
================================================================
Ejecutar con el Python del venv para confirmar que se está usando
el intérprete correcto y que todos los módulos críticos son visibles.

Uso (desde la raíz del proyecto):
    .\backend\venv\Scripts\python.exe backend\check_env.py
"""

import sys
import os

# ── 1. Información del intérprete ─────────────────────────────────────────────
print("=" * 60)
print("DIAGNÓSTICO DEL ENTORNO PYTHON")
print("=" * 60)
print(f"\n[1] Ejecutable Python en uso:\n    {sys.executable}")
print(f"\n[2] Versión de Python:\n    {sys.version}")
print(f"\n[3] Prefijo del entorno (debe contener 'venv'):\n    {sys.prefix}")
print(f"\n[4] VIRTUAL_ENV (variable de entorno):\n    {os.environ.get('VIRTUAL_ENV', 'No definida')}")

# ── 2. Rutas de búsqueda de módulos ──────────────────────────────────────────
print("\n[5] sys.path (rutas donde Python busca módulos):")
for i, p in enumerate(sys.path):
    print(f"    [{i}] {p}")

# ── 3. Verificación de imports críticos ──────────────────────────────────────
print("\n" + "=" * 60)
print("VERIFICACIÓN DE IMPORTS CRÍTICOS")
print("=" * 60)

modules = {
    "fastapi":                    "FastAPI (servidor web)",
    "uvicorn":                    "Uvicorn (servidor ASGI)",
    "pydantic":                   "Pydantic (validación de datos)",
    "dotenv":                     "python-dotenv (variables de entorno)",
    "langchain":                  "LangChain (núcleo + cadenas RAG)",
    "langchain_core":             "LangChain Core",
    "langchain_text_splitters":   "LangChain Text Splitters",
    "langchain_community":        "LangChain Community (loaders, vectorstores)",
    "langchain_huggingface":      "LangChain HuggingFace (embeddings locales)",
    "langchain_groq":             "LangChain Groq (ChatGroq / Llama 3)",
    "chromadb":                   "ChromaDB (base de datos vectorial)",
    "pypdf":                      "PyPDF (lectura de PDFs)",
    "sentence_transformers":      "Sentence-Transformers (modelo all-MiniLM-L6-v2)",
}

all_ok = True
for module, description in modules.items():
    try:
        imported = __import__(module)
        version = getattr(imported, "__version__", "versión no disponible")
        print(f"  ✔  {description}")
        print(f"       módulo: {module}  |  versión: {version}")
    except ImportError as e:
        all_ok = False
        print(f"  ✘  {description}")
        print(f"       módulo: {module}  |  ERROR: {e}")

# ── 4. Comprobación específica de las cadenas RAG ────────────────────────────
print("\n[Comprobación adicional] Cadenas RAG de LangChain:")
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    print("  ✔  create_retrieval_chain — OK")
    print("  ✔  create_stuff_documents_chain — OK")
except ImportError as e:
    all_ok = False
    print(f"  ✘  ERROR importando cadenas RAG: {e}")

# ── 5. Resumen final ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if all_ok:
    print("✔  RESULTADO: Entorno configurado correctamente.")
    print("   Puedes arrancar uvicorn sin problemas.")
else:
    print("✘  RESULTADO: Hay módulos faltantes.")
    print("   Ejecuta el rebuild_env.ps1 o instala manualmente:")
    print("   .\\backend\\venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt")
print("=" * 60 + "\n")
