# Arquitectura del Módulo de Ingesta de Datos (RAG)

El presente documento detalla el diseño arquitectónico y la implementación técnica de la primera fase del motor RAG (*Retrieval-Augmented Generation*) desarrollado para el Asistente Conversacional Vitivinícola. Esta fase comprende el subsistema de ingesta de normativas, boletines oficiales y guías técnicas agrarias en formato PDF, su posterior vectorización y almacenamiento persistente en una base de datos vectorial local.

---

## 1. Propósito del Subsistema

El endpoint `/documents/ingest` (accesible mediante el verbo HTTP `POST`) constituye el canal principal de alimentación de conocimiento del sistema. Su objetivo primordial es recibir documentos PDF no estructurados (tales como el BOE, normativas de la PAC o especificaciones del Cuaderno Digital de Explotación Agrícola) y transformarlos en fragmentos de información semánticamente indexados.

Esta indexación permite que, en fases posteriores, el asistente conversacional recupere de forma eficiente y precisa los artículos legales pertinentes para responder a las consultas de los viticultores, fundamentando sus respuestas en las fuentes normativas exactas.

---

## 2. Flujo de Procesamiento (Pipeline de Ingesta)

El proceso de transformación de un documento bruto en representaciones vectoriales sigue un flujo de trabajo secuencial, robusto y automatizado, orquestado a través del marco de trabajo LangChain.

```
┌────────────────────────────────────────────────────────┐
│            Recepción de Petición HTTP POST             │
│            (Fichero PDF via UploadFile)                │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             Validación de Tipo MIME & UUID             │
│        (Almacenamiento temporal en /backend/temp)      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                Extracción de Contenido                 │
│                 (PyPDFLoader)                          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               Segmentación de Documentos               │
│       (RecursiveCharacterTextSplitter: 1000/200)       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│                Vectorización Semántica                 │
│      (HuggingFaceEmbeddings: all-MiniLM-L6-v2)         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│              Almacenamiento Persistente                │
│            (ChromaDB en /backend/chroma_db)            │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│            Limpieza y Retorno de Respuesta             │
│            (Eliminación de PDF & IngestResponse)       │
└────────────────────────────────────────────────────────┘
```

El pipeline se desglosa en las siguientes etapas técnicas:

### 2.1. Recepción y Validación de Entrada
El sistema recibe la petición HTTP adjuntando un archivo mediante `multipart/form-data`. En primera instancia, se verifica el tipo MIME del documento (`application/pdf` o `application/octet-stream`). Si la validación falla, el servidor interrumpe la ejecución devolviendo una excepción HTTP 400 (`Bad Request`).

### 2.2. Almacenamiento Temporal Seguro
Para evitar colisiones de nombres ante peticiones concurrentes, el fichero se almacena en el directorio temporal local `/backend/temp` asignándole un identificador único universal (`UUID`) concatenado con el nombre original del archivo.

### 2.3. Extracción de Contenido (`PyPDFLoader`)
Se emplea la clase `PyPDFLoader` de LangChain para analizar el archivo almacenado en disco. Este componente extrae el texto plano del PDF estructurándolo en una lista de objetos `Document`, donde cada elemento representa una página individual del documento original y preserva metadatos clave (como el número de página y la ruta de origen).

### 2.4. Segmentación Avanzada (`RecursiveCharacterTextSplitter`)
Dado que los modelos de lenguaje y de embeddings poseen una ventana de contexto limitada, el texto extraído se somete a un proceso de división mediante `RecursiveCharacterTextSplitter`. Se han configurado los siguientes parámetros óptimos para la literatura legal agraria:
*   **Tamaño de fragmento (`chunk_size`):** 1000 caracteres. Garantiza que cada fragmento contenga suficiente contexto semántico (aproximadamente un artículo o cláusula normativa completa).
*   **Solapamiento (`chunk_overlap`):** 200 caracteres. Mantiene la coherencia contextual entre fragmentos adyacentes, evitando la pérdida de información en los límites de corte.

### 2.5. Generación de Embeddings (`HuggingFaceEmbeddings`)
Los fragmentos generados se transforman en vectores numéricos densos de alta dimensionalidad. Para ello se utiliza la clase `HuggingFaceEmbeddings` de LangChain ejecutando el modelo acústico-semántico `all-MiniLM-L6-v2`. Este proceso proyecta el texto en un espacio vectorial donde la proximidad geométrica refleja la similitud semántica.

### 2.6. Persistencia en Base de Datos Vectorial (`ChromaDB`)
Los vectores resultantes, junto con el texto original del fragmento y sus metadatos asociados, se indexan en una instancia de `Chroma` (ChromaDB). El motor se ha configurado para persistir la información de forma local en el directorio `/backend/chroma_db` bajo la colección `normativas_vitivinicolas`.

### 2.7. Retorno y Limpieza (`Teardown`)
El ciclo concluye asegurando la eliminación del archivo temporal del directorio `/backend/temp` mediante un bloque `finally`, garantizando la higiene del sistema de ficheros incluso ante eventuales fallos de ejecución. Finalmente, se retorna una respuesta JSON tipada mediante Pydantic (`IngestResponse`) que certifica el éxito de la operación e informa del número real de fragmentos indexados.

---

## 3. Decisiones de Arquitectura y Justificación Formal

### 3.1. Soberanía de Datos y Privacidad en el Sector Agrario
En la arquitectura del sistema, se ha optado de forma deliberada por la integración de un modelo de embeddings de código abierto ejecutado en local (`all-MiniLM-L6-v2` a través de `HuggingFaceEmbeddings`) frente a soluciones comerciales basadas en la nube, tales como los servicios de OpenAI (`text-embedding-3-small` o `ada-002`). Esta decisión arquitectónica se fundamenta en la estricta necesidad de preservar la confidencialidad y la soberanía de los datos agrarios. 

La información gestionada en el Cuaderno Digital de Explotación Agrícola (CUE) incluye datos de carácter sensible, tales como geolocalización de parcelas, rendimientos de cosecha, planes de fertilización, tratamientos fitosanitarios y estructuras de costes. La transmisión de estos datos a servidores externos de terceros (habitualmente sujetos a jurisdicciones fuera de la Unión Europea) plantea riesgos severos de cumplimiento normativo respecto al RGPD y expone el *know-how* estratégico de las explotaciones vitivinícolas. Al mantener el cómputo de los embeddings y el almacenamiento vectorial (ChromaDB) de forma 100% local, se garantiza el aislamiento perimetral de la información.

### 3.2. Viabilidad Económica y Eficiencia Computacional
Desde la perspectiva de la ingeniería de software y la viabilidad del proyecto, el uso de modelos locales elimina por completo la dependencia de facturación recurrente por uso de API (pago por *tokens*), asegurando la sostenibilidad económica del sistema a largo plazo para las cooperativas y pequeños viticultores. 

Asimismo, el modelo seleccionado (`all-MiniLM-L6-v2`) ofrece un equilibrio excepcional entre rendimiento semántico y coste computacional. Con un peso aproximado de 90 MB, permite su ejecución ágil en hardware de consumo estándar sin requerir aceleración por GPU dedicada, democratizando el despliegue del asistente RAG en entornos rurales o con infraestructura tecnológica limitada.

---

## 4. Contrato de Comunicación (Esquemas Pydantic)

El endpoint respeta estrictamente el contrato establecido en la especificación OpenAPI (`/api-spec/openapi.yaml`), implementando la validación y serialización de datos a través de Pydantic.

```python
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
```

La adopción de este tipado estricto asegura que los consumidores de la API (como la futura aplicación cliente desarrollada en Vite/React) dispongan de un contrato predecible y fuertemente tipado para gestionar la interfaz de usuario durante la carga del conocimiento normativo.
