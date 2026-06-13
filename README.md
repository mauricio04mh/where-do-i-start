# Where Do I Start

Proyecto Python para generar rutas de aprendizaje optimizadas.

## Relevancia de recomendaciones

El sistema conserva `target_topics` interpretados por el LLM para mejorar la
relevancia semantica de las rutas. El algoritmo greedy combina utilidad por
topico, coincidencia textual con el objetivo, prerrequisitos utiles,
preferencia de aprendizaje y dificultad esperada.

## CLI

Generar una ruta con Branch and Bound:

```bash
python -m src.main --student student-llm-apps --algorithm branch_and_bound
```

Comparar algoritmos manualmente:

```bash
python -m src.main --student student-chatbot-beginner --algorithm greedy
python -m src.main --student student-chatbot-beginner --algorithm branch_and_bound
python -m src.main --student student-chatbot-beginner --algorithm simulated_annealing
python -m src.main --student student-chatbot-beginner --algorithm ant_colony
python -m src.main --run-experiments
```

Debug de scoring sin generar ruta:

```bash
python -m src.main --student student-llm-apps --debug-scoring
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

## Docker Compose

Levantar backend y frontend juntos:

```bash
docker compose up --build
```

URLs:

- Frontend: http://127.0.0.1:5173
- Backend/API docs: http://127.0.0.1:8001/docs

El backend usa `network_mode: host` y sirve la API en el puerto `8001`. El
frontend proxy apunta a `http://host.docker.internal:8001`, asi que no
necesitas cambiar nada para que las llamadas a `/api` funcionen.

Detener servicios:

```bash
docker compose down
```

Endpoints principales:

- GET /students
- GET /resources
- POST /paths/generate
- POST /paths/debug-scoring
- POST /chat/ask

Ejemplo POST /paths/generate:

```json
{
  "student_id": "student-chatbot-beginner",
  "algorithm": "branch_and_bound",
  "use_llm": false
}
```

## LLM-assisted scoring

The system can optionally use Gemini or Ollama to score the semantic relevance of the
top-K rule-based candidates. It first ranks every resource with the deterministic
utility function, sends only the top-K candidates to the selected LLM in one batch call,
then combines rule-based utility with the LLM relevance score.

The combined utility is now centered on the neutral LLM score:
`final_utility = rule_based_utility + LLM_SCORE_WEIGHT * (llm_score - 5)`.
Scores above 5 boost a resource and scores below 5 penalize it. When LLM scoring
is enabled, root resources with final utility below `LLM_MIN_UTILITY_THRESHOLD`
are not added to the path, while prerequisites can still be included when they
are needed by a selected resource.

`llm_debug` records provider/model settings, score weight, top-K, the combined
ranking, and inconsistency metrics: missing neutral scores, low-relevance
selected resources, high LLM scores for off-topic resources, and the average LLM
score of selected resources.

Environment variables:

- `LLM_PROVIDER=gemini`
- `GEMINI_API_KEY=...`
- `GEMINI_MODEL=gemini-2.5-flash-lite`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=llama3.2:3b`
- `OLLAMA_TIMEOUT_SECONDS=120`
- `LLM_CANDIDATE_TOP_K=15`
- `LLM_SCORE_WEIGHT=1.0`
- `LLM_MIN_UTILITY_THRESHOLD=8.0`

Examples:

```bash
python -m src.main --student student-llm-apps --algorithm greedy --use-llm
python -m src.main --student student-llm-apps --algorithm branch_and_bound --use-llm
python -m src.main --student student-chatbot-beginner --algorithm simulated_annealing --use-llm
python -m src.main --student student-chatbot-beginner --algorithm ant_colony --use-llm
python -m src.main --student student-llm-apps --debug-scoring
python -m src.main --student student-llm-apps --debug-scoring --use-llm --llm-top-k 10 --llm-score-weight 2.0
python -m src.main --student student-llm-apps --debug-scoring --use-llm --llm-provider none
```

### Branch and Bound

Branch and Bound explores candidate learning paths recursively and uses an
optimistic upper bound based on fractional utility density to prune branches
that cannot improve the best solution found so far. It is slower than Greedy but
can find stronger paths on small and medium candidate sets.

### Simulated Annealing

Simulated Annealing starts from an initial greedy path, generates neighboring
paths by adding, removing, or replacing resources, and always accepts better
paths. When the temperature is high, it can also accept worse paths with a
decreasing probability. This helps the search escape local optima while still
returning the best valid path found.

### Ant Colony Optimization

Ant Colony Optimization construye rutas mediante varias hormigas artificiales.
Cada hormiga selecciona recursos validos segun una combinacion de feromona
acumulada y heuristica local. Las rutas de mayor calidad refuerzan los recursos
usados mediante feromonas, mientras que la evaporacion evita convergencia
prematura.

## Ollama with Docker

Start Ollama:

```bash
docker compose up -d ollama
```

Pull a model:

```bash
docker exec -it where-do-i-start-ollama ollama pull llama3.2:3b
```

Run the full app:

```bash
docker compose up --build
```

Use Ollama from the backend by setting `.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT_SECONDS=120
LLM_CANDIDATE_TOP_K=10
LLM_SCORE_WEIGHT=2.0
LLM_MIN_UTILITY_THRESHOLD=8.0
```

The backend uses `network_mode: host`, so `http://localhost:11434` reaches the
Ollama port exposed on the host by Docker Compose.

Debug scoring:

```bash
docker compose exec backend python -m src.main --student student-llm-apps --debug-scoring --use-llm
```

Generate path:

```bash
docker compose exec backend python -m src.main --student student-llm-apps --algorithm greedy --use-llm
docker compose exec backend python -m src.main --student student-llm-apps --algorithm branch_and_bound --use-llm
docker compose exec backend python -m src.main --student student-chatbot-beginner --algorithm simulated_annealing --use-llm
docker compose exec backend python -m src.main --student student-chatbot-beginner --algorithm ant_colony --use-llm
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
