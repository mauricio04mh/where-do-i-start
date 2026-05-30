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
