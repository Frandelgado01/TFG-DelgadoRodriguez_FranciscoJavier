Registro de Problemas y Soluciones (Backend & Entorno)
1. El .gitignore ignorado por Git (Problema de Codificación)
Síntoma: Al ejecutar git status, la carpeta venv/ seguía apareciendo como untracked a pesar de estar incluida en el archivo .gitignore.

Causa: Al crear o editar el archivo desde herramientas nativas de Windows (como el Bloc de notas), se guardó con una codificación diferente a UTF-8 (probablemente UTF-16 o con caracteres invisibles BOM). Git es incapaz de leer estas codificaciones y asume que el archivo está vacío o es inválido.

Solución: Se eliminó el archivo corrupto y se recreó directamente desde el explorador de archivos de VS Code, asegurando una codificación UTF-8 pura.

2. Conflicto de Entornos Virtuales Múltiples (VS Code "ciego")
Síntoma: VS Code mostraba 13 errores de tipo missing-import (subrayados en rojo) en main.py, a pesar de que las librerías estaban instaladas correctamente en la terminal.

Causa: Existían dos carpetas venv/: una en la raíz del proyecto y otra dentro de la carpeta backend/. El servidor de lenguaje de VS Code (Pylance) estaba leyendo el entorno vacío de la raíz, mientras que las instalaciones se estaban haciendo en el entorno del backend.

Solución: 1. Eliminación del entorno duplicado en la raíz.
2. Creación de un archivo de configuración explícito .vscode/settings.json con la directiva "python.defaultInterpreterPath": "backend/venv/Scripts/python.exe", forzando al editor a usar la ruta absoluta del entorno correcto.

3. Ejecución Global vs. Local de Uvicorn
Síntoma: Al levantar el servidor con el comando uvicorn main:app --reload, el proceso crasheaba inmediatamente lanzando errores en process.py y multiprocessing.

Causa: En Windows, escribir el comando a secas a veces invoca una instalación global de Uvicorn en el sistema operativo en lugar de la del entorno virtual activo, perdiendo el acceso a las dependencias instaladas.

Solución: Forzar el uso del motor de Python del entorno virtual mediante el módulo -m. El comando correcto y seguro es: python -m uvicorn main:app --reload (o indicando la ruta absoluta .\venv\Scripts\python.exe -m uvicorn...).

4. "Dependency Hell" con PyTorch y Versiones Estrictas
Síntoma: El comando pip install -r requirements.txt fallaba al intentar instalar torch==2.6.0+cpu y posteriormente lanzaba un error de ResolutionImpossible con LangChain.

Causa: 1. La versión ligera de PyTorch para CPU (+cpu) no reside en el índice principal de PyPi, sino en un servidor dedicado de Meta.
2. Fijar versiones exactas (==) en librerías de evolución rápida como el ecosistema LangChain provoca choques irresolubles para el gestor de paquetes.

Solución: 1. Instalar PyTorch manualmente apuntando a su índice específico: --index-url https://download.pytorch.org/whl/cpu.
2. "Relajar" el archivo requirements.txt quitando las versiones estrictas, permitiendo a pip resolver la matriz de compatibilidad dinámicamente.

5. Deprecación Arquitectónica de LangChain (El Jefe Final)
Síntoma: Error persistente ModuleNotFoundError: No module named 'langchain.chains' al importar create_retrieval_chain, incluso tras reinstalar con éxito todas las librerías desde cero.

Causa: LangChain ha sufrido una reestructuración severa en sus versiones recientes (0.2 a >0.3). Los módulos clásicos basados en langchain.chains han sido movidos, deprecados o eliminados del núcleo principal, rompiendo la compatibilidad hacia atrás en instalaciones limpias.

Solución: Refactorización completa de la lógica del RAG en el endpoint /ask. Se sustituyeron las cadenas clásicas por LCEL (LangChain Expression Language) puro, utilizando componentes modernos y estables (RunnablePassthrough, StrOutputParser) que se integran directamente en el langchain-core actual.