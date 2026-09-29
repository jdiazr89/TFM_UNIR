# Guia de aprendizaje del proyecto (detalle por archivo)

Este documento explica el proyecto archivo por archivo, con foco en entender flujo, responsabilidades y decisiones de implementacion.

## 1) app/__init__.py

- Contiene solo comentarios.
- Su funcion practica es marcar la carpeta app como paquete Python para habilitar imports como app.router_chat.

## 2) app/config.py

- Importa BaseSettings de pydantic_settings.
- Declara la clase Settings para centralizar configuracion.
- app_name define el nombre logico de la aplicacion.
- model_name define el modelo de Ollama que usa el cliente LLM.
- chroma_dir define la carpeta de persistencia de la memoria vectorial.
- Config.env_file = ".env" permite sobreescribir variables por entorno.
- settings = Settings() crea una instancia unica lista para inyeccion.

## 3) app/llm_client.py

- Importa requests para hacer HTTP POST a Ollama.
- Define la clase LLMClient con un constructor que guarda model_name.
- El metodo generate(prompt) envia el prompt al endpoint local de Ollama.
- stream=False solicita respuesta completa en una sola carga.
- num_predict=256 limita longitud para controlar latencia/costo.
- temperature=0.7 equilibra creatividad vs estabilidad.
- Devuelve response del JSON con fallback a cadena vacia.

## 4) app/memory.py

- Importa chromadb, PersistentClient, SentenceTransformer, tipados, re y os.
- Clase VectorMemory encapsula almacenamiento y recuperacion de recuerdos.

### Constructor

- Crea carpeta vector_memory si no existe.
- Inicializa cliente persistente de Chroma apuntando a vector_memory.
- Crea o recupera coleccion memories con distancia coseno.
- Carga modelo all-MiniLM-L6-v2 para embeddings.

### _embed(text)

- Codifica un texto en vector numerico usando SentenceTransformer.
- Retorna lista de floats (formato esperado por Chroma).

### store_memory(...)

- Construye metadata base con user_id y tipo.
- Si hay extra, fusiona claves (ejemplo: numero_pedido).
- Construye documento con formato Usuario/Compita.
- Genera embedding del documento completo.
- Inserta en Chroma con id incremental por usuario.

### retrieve_memories(user_id, query, top_k)

- Genera embedding de la consulta actual.
- Busca en Chroma solo documentos del mismo user_id.
- Devuelve top_k documentos mas cercanos semanticamente.

### get_last_order_for_user(user_id)

- Consulta por texto "pedido" y tipo pedido para ese usuario.
- Recorre documentos del mas reciente al mas antiguo.
- Extrae patron #12345 con regex.
- Devuelve el numero encontrado o None.

## 5) app/schemas.py

- Importa BaseModel y tipos.
- ChatRequest: user_id y message para endpoint /chat.
- ChatResponse: reply, used_memory y retrieved_memories.
- EvaluationRequest: user_id, scenario_id, messages.
- EvaluationResult: scenario_id, respuestas con/sin memoria y metricas.

## 6) app/router_chat.py

Este archivo contiene la logica principal de negocio y dos endpoints.

### Importaciones y estado global

- Importa APIRouter y HTTPException de FastAPI.
- Importa List y Optional.
- Importa re y random para parseo y simulacion de estado.
- Importa schemas, memoria, cliente LLM y settings.
- Crea router con prefijo /api.
- Instancia memory_manager y llm al cargar modulo.

### Reglas para pedidos

- ESTADOS_PEDIDO define estados posibles simulados.
- detectar_numero_pedido busca secuencias de 5-10 digitos.
- generar_respuesta_estado_pedido elige un estado aleatorio y formatea respuesta.
- es_consulta_pedido_anterior identifica frases como "mi ultimo pedido".

### Reglas de olvido de numero

- es_olvido_numero detecta frases de no recordar numero.
- generar_respuesta_olvido devuelve instrucciones concretas.

### Reglas de reclamo

- es_reclamo detecta vocabulario de inconformidad.
- generar_respuesta_reclamo pide datos minimos para tramitar.

### build_contextual_prompt

- Define prompt base con rol, objetivo, reglas e intenciones.
- Si hay recuerdos, los agrega como viñetas de contexto.
- Inserta mensaje del usuario al final.
- Cierra con "Respuesta del asistente:" para guiar al LLM.

### Endpoint POST /api/chat

Flujo interno:

- Limpia el mensaje y captura user_id.
- Detecta si hay numero de pedido.
- Recupera memoria relevante por similitud.
- Si usuario pide pedido anterior: intenta obtener ultimo pedido guardado.
- Si existe ultimo pedido, responde estado; si no, pide numero.
- Si el mensaje trae numero: responde estado de ese numero.
- Si pregunta estado sin numero: solicita el numero.
- Si detecta olvido: entrega guia de recuperacion.
- Si detecta reclamo: entrega plantilla de datos para resolver.
- En caso general: usa LLM con prompt contextual.
- En todos los casos, guarda memoria del turno.
- Retorna ChatResponse con indicador de uso de memoria.
- Maneja excepciones con HTTP 500 y detalle.

### Endpoint POST /api/evaluate

- Recorre los mensajes del escenario con memoria activada.
- En cada turno: recupera recuerdos, arma prompt, genera reply, guarda memoria.
- Repite la misma secuencia sin memoria (memories vacio).
- Devuelve respuestas de ambos modos.
- Actualmente sus metricas son fijas, por eso el analisis robusto se hace en eval/runner.py.

## 7) app/main.py

- Crea app FastAPI.
- Configura CORS abierto para facilitar pruebas frontend/local.
- Registra router de chat.
- En startup intenta un warm-up a Ollama con timeout corto.
- Si Ollama aun no esta listo, ignora error para no bloquear arranque.

## 8) app/evaluation.py (modulo legacy)

- Define modelos y pipeline de evaluacion alternativo.
- Replica idea de ejecutar con y sin memoria.
- No esta conectado a main/router en el flujo actual.
- Mantiene metricas hardcodeadas, similar a version inicial.

## 9) app/static/index.html

- Define estructura visual del cliente web.
- Carga Bootstrap y styles.css.
- Header muestra titulo y autores.
- Panel lateral: avatar, estado, indicador memoria y acciones rapidas.
- Panel principal: cabecera de chat, caja de mensajes e input.
- Carga app.js al final.

## 10) app/static/styles.css

- Define tipografia base del body.
- chat-card controla alto fijo y layout en columna.
- #chat-box habilita scroll y fondo suave.
- user-message y bot-message definen globos visuales.
- bot-temp da estilo a "Escribiendo...".
- avatar-bot define circulo azul con inicial.
- Personaliza scrollbar webkit.

## 11) app/static/app.js

- Define API_BASE del backend.
- Obtiene referencias DOM (chat, input, boton).
- appendMessage inserta mensajes en chat y hace autoscroll.
- removeTempMessages limpia indicadores temporales.
- sendMessage:
  - toma texto (manual o accion rapida), valida vacio.
  - pinta mensaje del usuario y estado "Escribiendo...".
  - hace POST a /api/chat con user_id fijo demo.
  - parsea respuesta JSON y gestiona errores HTTP.
  - muestra reply del asistente.
  - activa/desactiva indicador de memoria segun respuesta.
  - maneja error de red con mensaje de sistema.
- Agrega listeners para click y Enter.
- Configura botones de acciones rapidas.
- Inserta saludo inicial automatico del asistente.

## 12) eval/scenarios.py (actualizado)

- Contiene bateria de escenarios realistas y variados.
- Cada escenario define:
  - scenario_id unico.
  - category para analisis agregado.
  - memory_advantage_expected para control de sesgo.
  - messages como conversacion multivuelta.
  - expected_behavior en lenguaje natural.
  - checks con reglas objetivas sobre respuesta final.
- Tipos de checks implementados:
  - last_response_must_include_any
  - last_response_must_not_include_any
  - must_ask_question

## 13) eval/runner.py (actualizado)

- Ejecuta todos los escenarios contra /api/evaluate.
- Genera user_id unico por escenario y corrida para evitar contaminacion entre pruebas.
- Normaliza texto (minusculas + sin acentos) para checks robustos.
- Evalua respuesta final con reglas objetivas por escenario.
- Calcula score con memoria y score sin memoria.
- Calcula delta por escenario.
- Agrega resumen global:
  - promedio con memoria
  - promedio sin memoria
  - victorias/derrotas/empates
  - desglose por categoria
- Exporta resultados a:
  - eval/results/results.csv
  - eval/results/results.json
  - eval/results/summary.md
- Registra errores de ejecucion por escenario sin detener toda la corrida.

## 14) eval/eval_memory_vs_nomemory.py (actualizado)

- Script rapido para ejecutar un solo escenario por indice.
- Reutiliza lista de escenarios actual.
- Hace POST con timeout y validacion raise_for_status().
- Imprime JSON de comparacion con/sin memoria.

## 15) README.md

- Explica objetivo del TFM, tecnologias y arquitectura.
- Incluye pasos de instalacion y ejecucion.
- Contiene descripcion conceptual del rol de memoria vectorial en el asistente.

## 16) requirements.txt

- Lista dependencias clave para backend, inferencia y embeddings.
- Fija versiones para reproducibilidad.

## Flujo extremo a extremo

1. El frontend envia mensaje a /api/chat.
2. router_chat recupera memoria y aplica reglas de negocio.
3. Si no hay regla especial, delega al LLM con prompt contextual.
4. Se guarda el turno en memoria vectorial.
5. Para evaluacion, eval/runner.py invoca /api/evaluate en lote.
6. El runner aplica checks por escenario y produce reportes.

## Limites actuales y mejoras recomendadas

- /api/evaluate devuelve metricas fijas; el scoring real queda en runner.
- Estado de pedidos es aleatorio (simulacion), no conectado a sistema transaccional real.
- user_id fijo en frontend limita pruebas multiusuario.
- Conviene añadir tests automatizados (pytest) para reglas de negocio puras.

## Como usar la nueva evaluacion

1. Levanta FastAPI y Ollama.
2. Ejecuta: python eval/runner.py
3. Revisa:
   - eval/results/summary.md para panorama ejecutivo.
   - eval/results/results.csv para analisis tabular.
   - eval/results/results.json para trazabilidad completa.
