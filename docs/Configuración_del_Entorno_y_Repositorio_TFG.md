# **Configuración del Entorno y Estructura del Repositorio**

Este documento registra los primeros pasos técnicos en el desarrollo del Trabajo de Fin de Grado: **"Desarrollo de un Asistente Inteligente basado en RAG para la Gestión Normativa y de Sostenibilidad en el Sector Vitivinícola"**. Se detalla la configuración inicial del control de versiones y la estructura arquitectónica del proyecto.

## **1\. Arquitectura de Directorios**

Para cumplir con los principios de la metodología Spec-Driven Development (SDD) y mantener una clara separación de responsabilidades entre la lógica de negocio y la interfaz de usuario, se ha establecido la siguiente estructura en la rama principal (main) del repositorio GitHub:

| Directorio | Tecnología Principal | Propósito dentro del TFG   |
| :---- | :---- | :---- |
| frontend/ | React | Desarrollo de la interfaz de usuario web accesible. Consumirá la API documentada y mockeada. |
| backend/ | Python | Alojamiento del servidor, lógica de la arquitectura RAG y conexión con la base de datos vectorial. |
| api-spec/ | OpenAPI / YAML | Directorio central para el contrato SDD. Fuente de verdad para la comunicación entre cliente y servidor. |
| data/ | Local (PDF, DOCX) | Corpus documental vitivinícola (BOE, PAC, CUE) sin procesar. Ignorado en el control de versiones. |

## **2\. Resolución de Problemas en el Control de Versiones**

Git, por defecto, no rastrea directorios vacíos. Para inicializar la estructura arquitectónica en el repositorio remoto sin necesidad de añadir código fuente prematuro, se empleó la técnica de los archivos ocultos .gitkeep.  
Dado que el entorno de desarrollo operaba bajo **Windows PowerShell**, el comando Unix estándar (touch) no era compatible, lanzando un CommandNotFoundException. Se documenta la solución técnica aplicada:

### **Comandos Ejecutados en PowerShell:**

* Las carpetas fueron creadas manualmente en el explorador de archivos del sistema operativo.  
* Para generar los archivos ocultos de retención en PowerShell, se ejecutó:  
  New-Item frontend/.gitkeep, backend/.gitkeep, api-spec/.gitkeep \-ItemType File  
* Para salvaguardar la carpeta local de datos (y evitar subir documentos pesados o sensibles al repositorio público), se procedió a configurar la regla de exclusión:  
  Set-Content \-Path .gitignore \-Value "data/"

## **3\. Conclusión del Hito**

El repositorio TFG-DelgadoRodriguez\_FranciscoJavier.git cuenta ahora con una arquitectura base profesional, preparada para el diseño de la especificación API (SDD) y el posterior desarrollo en paralelo de los componentes frontend y backend.