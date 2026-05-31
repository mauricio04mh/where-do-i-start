# Where Do I Start

Proyecto Python para generar rutas de aprendizaje optimizadas.

## Relevancia de recomendaciones

El sistema conserva `target_topics` interpretados por el LLM para mejorar la
relevancia semantica de las rutas. El algoritmo greedy combina utilidad por
topico, coincidencia textual con el objetivo, prerrequisitos utiles,
preferencia de aprendizaje y dificultad esperada.

## CLI

Generar una ruta con backtracking:

```bash
python -m src.main --student student-chatbot-beginner --algorithm backtracking
```

Comparar algoritmos manualmente:

```bash
python -m src.main --student student-chatbot-beginner --algorithm greedy
python -m src.main --student student-chatbot-beginner --algorithm backtracking
python -m src.main --run-experiments
```

## API Backend

Instalación:

```bash
pip install -r requirements.txt
```

Ejecución:

```bash
uvicorn src.api.app:app --reload
```

Abrir documentación:

http://127.0.0.1:8000/docs

Endpoints principales:

- GET /students
- GET /resources
- POST /paths/generate
- POST /chat/ask

Ejemplo POST /paths/generate:

```json
{
  "student_id": "student-chatbot-beginner",
  "algorithm": "backtracking",
  "use_llm": false
}
```

## Frontend

Instalar dependencias:

```bash
cd frontend
npm install
```

Ejecutar frontend:

```bash
npm run dev
```

Backend requerido:

```bash
uvicorn src.api.app:app --reload
```

URLs:

- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Frontend: http://127.0.0.1:5173

El frontend usa Vite con proxy: las llamadas a `/api` se redirigen a `http://127.0.0.1:8000` y se elimina el prefijo `/api`.
