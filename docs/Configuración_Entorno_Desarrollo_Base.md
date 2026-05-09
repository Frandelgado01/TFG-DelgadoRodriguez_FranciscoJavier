# **Configuración del Entorno de Desarrollo Base**

Este documento detalla la inicialización de los entornos de desarrollo para el Trabajo de Fin de Grado: **"Desarrollo de un Asistente Inteligente basado en RAG para la Gestión Normativa y de Sostenibilidad en el Sector Vitivinícola"**. Se ha establecido la base técnica tanto para el servidor backend como para la interfaz de usuario frontend, utilizando tecnologías modernas y estandarizadas.

## **1\. Backend: Entorno Python y Dependencias RAG**

Para el servidor, que albergará la lógica de la Inteligencia Artificial (LLM) y el motor de búsqueda vectorial, se ha optado por un entorno aislado y un stack tecnológico centrado en el rendimiento y la interoperabilidad (SDD).

### **Pasos de configuración ejecutados:**

1. **Creación de Entorno Virtual:** Se ha generado un entorno aislado mediante python \-m venv venv para evitar conflictos con otras dependencias del sistema operativo.  
2. **Instalación del Stack Tecnológico Base:**  
   * fastapi y uvicorn: Para desplegar la API RESTful de alto rendimiento que servirá de contrato (Spec-Driven Development).  
   * langchain, langchain-community y langchain-openai: El *framework* estándar de la industria para orquestar la arquitectura RAG y la comunicación con el LLM.  
   * chromadb: La base de datos vectorial embebida elegida para almacenar los *embeddings* de las normativas vitivinícolas y realizar la recuperación semántica.  
3. **Congelación de Dependencias:** Se ha generado el archivo requirements.txt para garantizar la reproducibilidad del entorno.

## **2\. Frontend: Inicialización del Proyecto React**

Para cumplir con las competencias de TI relativas a usabilidad y creación de servicios web interactivos, se ha inicializado una aplicación web moderna orientada a componentes.

### **Pasos de configuración ejecutados:**

1. **Scaffolding con Vite:** Se ha utilizado npm create vite@latest con el *template* de React. Se ha seleccionado Vite por su drástica reducción de los tiempos de compilación frente a herramientas tradicionales.  
2. **Despliegue Local:** El servidor de desarrollo se ha inicializado correctamente en el puerto local http://localhost:5173/.  
3. **Instalación de Librerías Críticas:**  
   * axios: Cliente HTTP configurado para realizar las peticiones a la API del backend en Python, consumiendo los endpoints definidos en el contrato SDD.  
   * react-markdown: Librería esencial para renderizar las respuestas complejas del chatbot generadas por el LLM, permitiendo mostrar de forma estilizada listas, tablas o citas a normativas legales (BOE, PAC).

## **3\. Conclusión del Hito**

Con la arquitectura de carpetas y los entornos de desarrollo virtualizados e inicializados tanto en cliente como en servidor, el proyecto está técnicamente preparado para comenzar la implementación de la Especificación de la API (SDD) y el diseño de la interfaz de usuario.