#  Diseño y evaluación de un asistente conversacional con memoria persistente para atención al cliente
### Proyecto de TFM — UNIR  
Autores: Diego José Leiva Espín, Junior Alberto Díaz Rojas, Yuly Astrid Ballén González

---

## Descripción del proyecto

Compita es un asistente virtual de atención al cliente desarrollado con **FastAPI**, **LLMs**, **memoria vectorial persistente** y técnicas modernas de **RAG (Retrieval-Augmented Generation)**.  
El objetivo del proyecto es demostrar cómo un agente conversacional puede mantener contexto, recordar interacciones previas y ofrecer respuestas coherentes y personalizadas sin necesidad de reentrenar el modelo base.

El sistema está diseñado con una arquitectura modular que permite su integración futura con sistemas empresariales como ERPs, CRMs o bases de datos corporativas.

---

## Tecnologías utilizadas

- **Python 3.10+**
- **FastAPI**
- **Uvicorn**
- **ChromaDB (PersistentClient)**
- **SentenceTransformers**
- **Ollama (Llama 3.1)**
- **HTML + CSS + JavaScript (Frontend)**
- **RAG (Recuperación aumentada de contexto)**

---

## Arquitectura general

El sistema se compone de:

- **Backend (FastAPI)**  
  Maneja la lógica conversacional, memoria, reglas y comunicación con el modelo LLM.

- **Memoria vectorial (ChromaDB)**  
  Almacena embeddings de interacciones para mantener continuidad conversacional.

- **Modelo de lenguaje (Ollama + Llama 3.1)**  
  Genera respuestas cuando no aplica una regla específica.

- **Frontend web**  
  Interfaz amigable para el usuario final.

---

## Estructura del proyecto

/app
├── main.py
├── router_chat.py
├── memory.py
├── llm_client.py
├── schemas.py
├── config.py
/frontend
├── index.html
├── styles.css
├── script.js
requirements.txt
README.md


## Instalación y ejecución

1️⃣ Crear entorno virtual
bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

2️⃣ Instalar dependencias
bash
pip install -r requirements.txt
3️⃣ Iniciar Ollama y descargar el modelo
bash
ollama pull llama3.1
4️⃣ Ejecutar el servidor FastAPI
bash
uvicorn app.main:app --reload
5️⃣ Abrir el frontend
Abrir frontend/index.html en el navegador.

---

## Evaluación robusta (memoria vs no memoria)

Se incorporó una batería de escenarios más realista para evitar resultados artificialmente favorables.

### Qué cambia

- Los escenarios mezclan casos de:
  - contradicción (preferencias que cambian)
  - información obsoleta
  - ruido conversacional
  - consultas irrelevantes
  - entidades similares (riesgo de confusión)
  - casos neutrales de control
- El análisis no depende de métricas fijas del backend.
- El script de evaluación calcula puntuaciones objetivas por reglas de verificación (checks).

### Archivos de evaluación

- eval/scenarios.py
- eval/runner.py
- eval/eval_memory_vs_nomemory.py

### Cómo ejecutar

1. Levantar backend:

  uvicorn app.main:app --reload

2. Ejecutar la batería:

  python eval/runner.py

### Salidas generadas

- eval/results/results.csv
- eval/results/results.json
- eval/results/summary.md

El archivo summary.md resume cantidad de escenarios ejecutados, promedio con memoria, promedio sin memoria, delta y desglose por categoría.

---

## Guía de aprendizaje del código

Para estudiar el proyecto archivo por archivo, revisa:

- GUIA_APRENDIZAJE_PROYECTO.md

Incluye explicación detallada de responsabilidades, flujo extremo a extremo y cómo se conectan backend, memoria, LLM y evaluación.

