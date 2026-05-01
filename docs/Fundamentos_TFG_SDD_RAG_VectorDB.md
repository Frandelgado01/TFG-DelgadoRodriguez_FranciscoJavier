# 

Marco Teórico y Fundamentos Tecnológicos

Este documento recoge los pilares teóricos para el Trabajo de Fin de Grado: **"Desarrollo de un Asistente Inteligente basado en RAG para la Gestión Normativa y de Sostenibilidad en el Sector Vitivinícola"**. Aquí se detallan las metodologías y arquitecturas clave que sustentan la solución, alineadas con las competencias de la Intensificación de Tecnologías de la Información.

## **1\. Metodología SDD (Spec-Driven Development)**

El Desarrollo Impulsado por Especificaciones (SDD) es un paradigma de ingeniería de software donde el diseño de la interfaz de programación de aplicaciones (API) precede a la implementación de cualquier código funcional. La "fuente de verdad" es un documento estandarizado (habitualmente OpenAPI o Swagger) que define los contratos de comunicación.

### **Aplicación en el Proyecto (React \+ Python)**

Dado que el proyecto separa la capa de presentación (React) de la lógica de negocio (Python), SDD proporciona las siguientes ventajas críticas:

* **Desarrollo Paralelo:** Permite al equipo de frontend (React) construir interfaces utilizando datos simulados (*mocks*) basados en la especificación, mientras el backend (Python) implementa la lógica real y las conexiones a los modelos de IA.  
* **Validación de Contratos:** Garantiza que las peticiones y respuestas sigan un esquema estricto, reduciendo los errores de integración y mejorando la mantenibilidad.  
* **Documentación Automática:** El propio archivo de especificación sirve como documentación técnica rigurosa para la memoria del TFG.

| Característica | Desarrollo Tradicional | Spec-Driven Development (SDD) |
| :---- | :---- | :---- |
| Punto de Partida | Escritura de código base | Diseño del contrato/API (YAML/JSON) |
| Sincronización Front/Back | Dependiente y secuencial (cuellos de botella) | Independiente y paralela |

## **2\. Arquitectura RAG (Retrieval-Augmented Generation)**

La Generación Aumentada por Recuperación (RAG) es un marco de trabajo de Inteligencia Artificial que mejora la calidad y veracidad de las respuestas de un Modelo de Lenguaje (LLM) anclándolo a fuentes de conocimiento externas, dinámicas y verificables antes de generar una respuesta.

### **Mitigación de Alucinaciones en el Entorno Legal**

En dominios críticos como el sector vitivinícola (que depende de la normativa PAC, BOE, Cuaderno Digital de Explotación \- CUE, y certificaciones ecológicas), la precisión es innegociable. Un LLM estándar puede generar respuestas plausibles pero legalmente incorrectas (fenómeno conocido como "alucinación"). RAG elimina este riesgo forzando al modelo a construir su respuesta basándose **exclusivamente** en los textos recuperados del corpus documental.

### **\[Image of Retrieval-Augmented Generation RAG architecture flowchart\]**

Fases de la Arquitectura RAG

1. **Ingesta y Procesamiento:** Los documentos complejos se procesan, se limpian y se dividen en fragmentos de texto con sentido semántico (*chunks*). Estos fragmentos se transforman en representaciones numéricas.  
2. **Recuperación (Retrieval):** Cuando un usuario (ej. un viticultor) hace una consulta, el sistema busca en la base de datos los fragmentos más relevantes para esa duda específica.  
3. **Generación Aumentada (Generation):** El LLM recibe la pregunta original del usuario empacada junto con los fragmentos legales recuperados (contexto) y elabora una respuesta fundamentada, permitiendo además citar la fuente exacta.

## **3\. Bases de Datos Vectoriales y Embeddings**

Las bases de datos vectoriales son la infraestructura de almacenamiento especializada necesaria para la fase de recuperación del RAG. Están diseñadas para almacenar y consultar vectores matemáticos de alta dimensionalidad (*embeddings*).

### **Búsqueda Semántica vs. Lexical**

A diferencia de las bases de datos tradicionales (SQL/NoSQL) que buscan coincidencias exactas de texto (lexical), las bases de datos vectoriales calculan distancias matemáticas para evaluar la similitud de conceptos (semántica). Por ejemplo, si el usuario consulta por "normas para uva orgánica", el sistema puede recuperar un fragmento sobre "regulación de viñedos ecológicos" porque, aunque las palabras difieren, sus vectores están próximos en el espacio multidimensional.  
\[Image of vector embeddings space showing semantic similarity\]  
La integración de sistemas como ChromaDB, Pinecone o Milvus en el backend de Python permitirá gestionar eficazmente el conocimiento del asistente, satisfaciendo el requisito de TI sobre gestión de sistemas de información con criterios de calidad y rendimiento.