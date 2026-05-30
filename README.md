# Where Do I Start

Proyecto Python para generar rutas de aprendizaje optimizadas.

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
  "algorithm": "greedy",
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
