import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "title",
    "topic",
    "duration_hours",
    "difficulty",
    "prerequisites",
    "description",
    "type",
    "utility",
}


NEW_RESOURCES: list[dict[str, Any]] = [
    {
        "id": "llm-api-quickstart",
        "title": "LLM API Quickstart",
        "topic": "LLMs",
        "duration_hours": 3,
        "difficulty": 2,
        "prerequisites": ["python-basics"],
        "description": "Call an LLM API from Python, pass messages, manage API keys, and inspect basic responses.",
        "type": "workshop",
        "utility": 0.48,
    },
    {
        "id": "llm-token-context-reading",
        "title": "Tokens, Context Windows, and Limits",
        "topic": "LLMs",
        "duration_hours": 2,
        "difficulty": 3,
        "prerequisites": ["llm-fundamentals"],
        "description": "Understand token budgets, context windows, truncation, latency, and why prompt length affects cost.",
        "type": "reading",
        "utility": 0.38,
    },
    {
        "id": "prompt-patterns-cookbook",
        "title": "Prompt Patterns Cookbook",
        "topic": "LLMs",
        "duration_hours": 5,
        "difficulty": 3,
        "prerequisites": ["prompt-engineering"],
        "description": "Practice reusable prompt patterns for extraction, classification, planning, critique, and refinement.",
        "type": "workshop",
        "utility": 0.62,
    },
    {
        "id": "llm-evaluation-basics",
        "title": "LLM Evaluation Basics",
        "topic": "LLMs",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["prompt-engineering"],
        "description": "Build small evaluation sets, define rubrics, compare model outputs, and track regressions.",
        "type": "course",
        "utility": 0.66,
    },
    {
        "id": "function-calling-workshop",
        "title": "Function Calling and Tool Use",
        "topic": "LLMs",
        "duration_hours": 7,
        "difficulty": 4,
        "prerequisites": ["structured-llm-output", "api-design"],
        "description": "Connect LLM responses to typed tools, validate arguments, handle retries, and recover from tool errors.",
        "type": "workshop",
        "utility": 0.72,
    },
    {
        "id": "llm-agent-foundations",
        "title": "LLM Agent Foundations",
        "topic": "LLMs",
        "duration_hours": 8,
        "difficulty": 4,
        "prerequisites": ["prompt-engineering", "data-structures-intro"],
        "description": "Study planning loops, tool selection, memory boundaries, and failure modes in agentic workflows.",
        "type": "course",
        "utility": 0.7,
    },
    {
        "id": "small-llm-local-lab",
        "title": "Run a Small Local LLM",
        "topic": "LLMs",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["llm-fundamentals", "docker-basics"],
        "description": "Run a local language model, compare latency and quality, and learn when local inference is useful.",
        "type": "workshop",
        "utility": 0.58,
    },
    {
        "id": "llm-capstone-assistant",
        "title": "Capstone: Personal LLM Assistant",
        "topic": "LLMs",
        "duration_hours": 14,
        "difficulty": 5,
        "prerequisites": ["llm-chatbot-project", "structured-llm-output"],
        "description": "Build an assistant that uses structured outputs, prompt templates, conversation state, and evaluation checks.",
        "type": "project",
        "utility": 0.92,
    },
    {
        "id": "cost-latency-optimization",
        "title": "Cost and Latency Optimization for LLM Apps",
        "topic": "LLMs",
        "duration_hours": 4,
        "difficulty": 4,
        "prerequisites": ["llm-api-quickstart", "llm-evaluation-basics"],
        "description": "Compare model choices, caching, prompt length, batching, and response constraints under product limits.",
        "type": "reading",
        "utility": 0.55,
    },
    {
        "id": "document-ingestion-basics",
        "title": "Document Ingestion Basics",
        "topic": "RAG",
        "duration_hours": 4,
        "difficulty": 3,
        "prerequisites": ["python-basics", "text-preprocessing"],
        "description": "Load PDFs, markdown, and text files, normalize content, and preserve source metadata for retrieval.",
        "type": "workshop",
        "utility": 0.54,
    },
    {
        "id": "chunking-strategies-rag",
        "title": "Chunking Strategies for RAG",
        "topic": "RAG",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["embeddings-intro", "document-ingestion-basics"],
        "description": "Compare fixed, semantic, and structure-aware chunking strategies for retrieval quality and cost.",
        "type": "workshop",
        "utility": 0.63,
    },
    {
        "id": "retrieval-evaluation-reading",
        "title": "Retrieval Evaluation Reading",
        "topic": "RAG",
        "duration_hours": 3,
        "difficulty": 4,
        "prerequisites": ["rag-fundamentals"],
        "description": "Learn recall, precision, hit rate, answer faithfulness, and the limits of manual spot checks.",
        "type": "reading",
        "utility": 0.5,
    },
    {
        "id": "hybrid-search-workshop",
        "title": "Hybrid Search Workshop",
        "topic": "RAG",
        "duration_hours": 7,
        "difficulty": 4,
        "prerequisites": ["vector-databases", "databases-sql"],
        "description": "Combine keyword search, vector search, metadata filters, and ranking rules in a single retriever.",
        "type": "workshop",
        "utility": 0.7,
    },
    {
        "id": "metadata-filtering-rag",
        "title": "Metadata Filtering for RAG",
        "topic": "RAG",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["vector-databases", "database-design"],
        "description": "Design metadata schemas and filters for access control, freshness, source type, and product context.",
        "type": "workshop",
        "utility": 0.62,
    },
    {
        "id": "reranking-for-rag",
        "title": "Reranking for Better RAG Answers",
        "topic": "RAG",
        "duration_hours": 6,
        "difficulty": 5,
        "prerequisites": ["rag-fundamentals"],
        "description": "Use rerankers and candidate selection to improve answer relevance when first-stage retrieval is noisy.",
        "type": "course",
        "utility": 0.68,
    },
    {
        "id": "rag-observability-lab",
        "title": "RAG Observability Lab",
        "topic": "RAG",
        "duration_hours": 8,
        "difficulty": 5,
        "prerequisites": ["rag-fundamentals", "llm-evaluation-basics"],
        "description": "Log queries, retrieved chunks, scores, generated answers, and user feedback for debugging RAG behavior.",
        "type": "workshop",
        "utility": 0.76,
    },
    {
        "id": "knowledge-base-rag-project",
        "title": "Project: Knowledge Base RAG",
        "topic": "RAG",
        "duration_hours": 12,
        "difficulty": 5,
        "prerequisites": ["rag-fundamentals", "document-ingestion-basics"],
        "description": "Build a searchable knowledge base over documents with ingestion, retrieval, generation, and citations.",
        "type": "project",
        "utility": 0.88,
    },
    {
        "id": "multi-source-rag-project",
        "title": "Project: Multi-Source RAG System",
        "topic": "RAG",
        "duration_hours": 16,
        "difficulty": 5,
        "prerequisites": ["knowledge-base-rag-project", "metadata-filtering-rag"],
        "description": "Integrate multiple document sources, metadata policies, reranking, and evaluation into one RAG system.",
        "type": "project",
        "utility": 0.96,
    },
    {
        "id": "rag-security-privacy",
        "title": "RAG Security and Privacy",
        "topic": "RAG",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["privacy-and-data-handling", "rag-fundamentals"],
        "description": "Identify leakage risks, prompt injection, document permissions, and safe logging practices for RAG.",
        "type": "course",
        "utility": 0.64,
    },
    {
        "id": "rag-fast-prototype",
        "title": "Fast RAG Prototype",
        "topic": "RAG",
        "duration_hours": 4,
        "difficulty": 4,
        "prerequisites": ["embeddings-intro", "prompt-engineering"],
        "description": "Create a minimal RAG prototype quickly to compare against longer, higher-quality build paths.",
        "type": "project",
        "utility": 0.56,
    },
    {
        "id": "chatbot-ui-flow-sketch",
        "title": "Chatbot UI Flow Sketch",
        "topic": "AI Chatbots",
        "duration_hours": 2,
        "difficulty": 2,
        "prerequisites": ["chatbot-concepts"],
        "description": "Sketch greeting, fallback, clarification, escalation, and completion flows before implementation.",
        "type": "reading",
        "utility": 0.35,
    },
    {
        "id": "conversation-state-workshop",
        "title": "Conversation State Workshop",
        "topic": "AI Chatbots",
        "duration_hours": 5,
        "difficulty": 3,
        "prerequisites": ["chatbot-concepts", "python-basics"],
        "description": "Track user turns, slot values, conversation branches, and session state in a Python chatbot.",
        "type": "workshop",
        "utility": 0.57,
    },
    {
        "id": "faq-chatbot-no-llm",
        "title": "FAQ Chatbot without an LLM",
        "topic": "AI Chatbots",
        "duration_hours": 6,
        "difficulty": 3,
        "prerequisites": ["rule-based-chatbot-project"],
        "description": "Build a deterministic FAQ chatbot with keyword matching, fallback responses, and simple analytics.",
        "type": "project",
        "utility": 0.6,
    },
    {
        "id": "llm-chatbot-api-integration",
        "title": "LLM Chatbot API Integration",
        "topic": "AI Chatbots",
        "duration_hours": 7,
        "difficulty": 4,
        "prerequisites": ["llm-api-quickstart", "api-design", "chatbot-concepts"],
        "description": "Connect a chatbot interface to an LLM API through a backend endpoint with request validation.",
        "type": "workshop",
        "utility": 0.72,
    },
    {
        "id": "chatbot-memory-patterns",
        "title": "Chatbot Memory Patterns",
        "topic": "AI Chatbots",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["llm-chatbot-project", "databases-sql"],
        "description": "Compare short-term context, stored preferences, summaries, and retrieval-backed memory.",
        "type": "course",
        "utility": 0.68,
    },
    {
        "id": "multimodal-chatbot-concepts",
        "title": "Multimodal Chatbot Concepts",
        "topic": "AI Chatbots",
        "duration_hours": 4,
        "difficulty": 4,
        "prerequisites": ["llm-fundamentals", "chatbot-concepts"],
        "description": "Explore image, audio, and document inputs for chatbot workflows and when they add product value.",
        "type": "reading",
        "utility": 0.48,
    },
    {
        "id": "support-chatbot-evaluation",
        "title": "Support Chatbot Evaluation",
        "topic": "AI Chatbots",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["llm-chatbot-project", "llm-evaluation-basics"],
        "description": "Evaluate helpfulness, refusal quality, escalation behavior, and answer consistency for support bots.",
        "type": "workshop",
        "utility": 0.66,
    },
    {
        "id": "production-chatbot-project",
        "title": "Project: Production Chatbot Backend",
        "topic": "AI Chatbots",
        "duration_hours": 14,
        "difficulty": 5,
        "prerequisites": [
            "llm-chatbot-project",
            "authentication-basics",
            "privacy-and-data-handling"
        ],
        "description": "Build a chatbot backend with authentication, persistence, logs, privacy controls, and evaluation hooks.",
        "type": "project",
        "utility": 0.92,
    },
    {
        "id": "rag-support-chatbot",
        "title": "Project: RAG Support Chatbot",
        "topic": "AI Chatbots",
        "duration_hours": 16,
        "difficulty": 5,
        "prerequisites": ["rag-chatbot-project", "knowledge-base-rag-project"],
        "description": "Build a support chatbot that grounds answers in product documents and reports unsupported questions.",
        "type": "project",
        "utility": 0.97,
    },
    {
        "id": "http-foundations-reading",
        "title": "HTTP Foundations for Backend Developers",
        "topic": "Backend Development",
        "duration_hours": 3,
        "difficulty": 2,
        "prerequisites": ["command-line-basics"],
        "description": "Learn requests, responses, methods, status codes, headers, and basic debugging with HTTP clients.",
        "type": "reading",
        "utility": 0.42,
    },
    {
        "id": "backend-python-service",
        "title": "Build a Python Backend Service",
        "topic": "Backend Development",
        "duration_hours": 6,
        "difficulty": 3,
        "prerequisites": ["python-basics", "git-foundations"],
        "description": "Create a small Python service with routes, configuration, tests, and a simple in-memory data store.",
        "type": "project",
        "utility": 0.58,
    },
    {
        "id": "api-validation-workshop",
        "title": "API Validation Workshop",
        "topic": "Backend Development",
        "duration_hours": 4,
        "difficulty": 3,
        "prerequisites": ["api-design"],
        "description": "Validate request payloads, return useful errors, and design contracts that clients can rely on.",
        "type": "workshop",
        "utility": 0.55,
    },
    {
        "id": "async-api-patterns",
        "title": "Async API Patterns",
        "topic": "Backend Development",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["fastapi-basics"],
        "description": "Use async handlers, timeouts, cancellation boundaries, and concurrency limits in Python APIs.",
        "type": "course",
        "utility": 0.65,
    },
    {
        "id": "background-jobs-workshop",
        "title": "Background Jobs Workshop",
        "topic": "Backend Development",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["fastapi-basics"],
        "description": "Move long-running work into background jobs and expose job status through backend endpoints.",
        "type": "workshop",
        "utility": 0.6,
    },
    {
        "id": "backend-database-integration",
        "title": "Backend Database Integration",
        "topic": "Backend Development",
        "duration_hours": 8,
        "difficulty": 4,
        "prerequisites": ["fastapi-basics", "database-design"],
        "description": "Connect APIs to relational databases with schemas, repositories, migrations, and error handling.",
        "type": "workshop",
        "utility": 0.75,
    },
    {
        "id": "authz-permissions-lab",
        "title": "Authorization and Permissions Lab",
        "topic": "Backend Development",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["authentication-basics"],
        "description": "Model roles, ownership checks, and permission policies for protected backend routes.",
        "type": "workshop",
        "utility": 0.66,
    },
    {
        "id": "ai-backend-gateway",
        "title": "Project: AI Backend Gateway",
        "topic": "Backend Development",
        "duration_hours": 10,
        "difficulty": 4,
        "prerequisites": ["fastapi-basics", "llm-api-quickstart"],
        "description": "Build a backend gateway that wraps AI provider calls, validation, rate limits, and response formatting.",
        "type": "project",
        "utility": 0.84,
    },
    {
        "id": "backend-capstone-ai-app",
        "title": "Capstone: Backend for an AI App",
        "topic": "Backend Development",
        "duration_hours": 15,
        "difficulty": 5,
        "prerequisites": [
            "ai-backend-gateway",
            "backend-database-integration",
            "testing-debugging"
        ],
        "description": "Deliver an AI application backend with persistence, validation, tests, and operational boundaries.",
        "type": "project",
        "utility": 0.94,
    },
    {
        "id": "numpy-data-foundations",
        "title": "NumPy Foundations for Data Work",
        "topic": "Data Science",
        "duration_hours": 4,
        "difficulty": 2,
        "prerequisites": ["python-basics"],
        "description": "Use arrays, vectorized operations, indexing, and numeric summaries as a bridge into data analysis.",
        "type": "course",
        "utility": 0.5,
    },
    {
        "id": "exploratory-data-analysis",
        "title": "Exploratory Data Analysis Workshop",
        "topic": "Data Science",
        "duration_hours": 6,
        "difficulty": 3,
        "prerequisites": ["data-analysis-pandas"],
        "description": "Profile datasets, detect missingness, compare distributions, and frame analysis questions.",
        "type": "workshop",
        "utility": 0.64,
    },
    {
        "id": "data-cleaning-workshop",
        "title": "Data Cleaning Workshop",
        "topic": "Data Science",
        "duration_hours": 5,
        "difficulty": 3,
        "prerequisites": ["data-analysis-pandas"],
        "description": "Handle missing values, duplicates, inconsistent categories, outliers, and reproducible cleaning steps.",
        "type": "workshop",
        "utility": 0.62,
    },
    {
        "id": "analytics-report-project",
        "title": "Project: Analytics Report",
        "topic": "Data Science",
        "duration_hours": 10,
        "difficulty": 4,
        "prerequisites": ["data-analysis-pandas", "data-visualization"],
        "description": "Analyze a dataset and produce a concise report with charts, assumptions, findings, and caveats.",
        "type": "project",
        "utility": 0.78,
    },
    {
        "id": "sql-for-analytics",
        "title": "SQL for Analytics",
        "topic": "Data Science",
        "duration_hours": 4,
        "difficulty": 3,
        "prerequisites": ["databases-sql"],
        "description": "Write analytical queries with joins, aggregation, filtering, window functions, and reusable views.",
        "type": "workshop",
        "utility": 0.52,
    },
    {
        "id": "ml-workflow-scikit",
        "title": "Scikit-Learn Workflow Workshop",
        "topic": "Machine Learning",
        "duration_hours": 7,
        "difficulty": 4,
        "prerequisites": ["machine-learning-intro"],
        "description": "Build train-test workflows with pipelines, preprocessing, estimators, and repeatable experiments.",
        "type": "workshop",
        "utility": 0.7,
    },
    {
        "id": "baseline-model-project",
        "title": "Project: Baseline ML Model",
        "topic": "Machine Learning",
        "duration_hours": 8,
        "difficulty": 4,
        "prerequisites": ["machine-learning-intro", "data-cleaning-workshop"],
        "description": "Train a baseline model, compare it to simple heuristics, and document first error patterns.",
        "type": "project",
        "utility": 0.74,
    },
    {
        "id": "classification-metrics-lab",
        "title": "Classification Metrics Lab",
        "topic": "Machine Learning",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["model-evaluation"],
        "description": "Choose and interpret classification metrics under class imbalance and business constraints.",
        "type": "workshop",
        "utility": 0.64,
    },
    {
        "id": "feature-selection-reading",
        "title": "Feature Selection Reading",
        "topic": "Machine Learning",
        "duration_hours": 3,
        "difficulty": 4,
        "prerequisites": ["feature-engineering"],
        "description": "Review filter, wrapper, embedded, and leakage-aware approaches to selecting model features.",
        "type": "reading",
        "utility": 0.43,
    },
    {
        "id": "end-to-end-ml-project",
        "title": "Project: End-to-End ML System",
        "topic": "Machine Learning",
        "duration_hours": 16,
        "difficulty": 5,
        "prerequisites": ["feature-engineering", "model-evaluation"],
        "description": "Build a full ML project from data preparation through training, evaluation, reporting, and packaging.",
        "type": "project",
        "utility": 0.95,
    },
    {
        "id": "env-config-secrets",
        "title": "Environment Configuration and Secrets",
        "topic": "Deployment",
        "duration_hours": 3,
        "difficulty": 3,
        "prerequisites": ["deployment-fundamentals"],
        "description": "Manage environment variables, secrets, config files, and local production parity for deployed apps.",
        "type": "reading",
        "utility": 0.46,
    },
    {
        "id": "docker-compose-workshop",
        "title": "Docker Compose Workshop",
        "topic": "Deployment",
        "duration_hours": 5,
        "difficulty": 3,
        "prerequisites": ["docker-basics"],
        "description": "Run APIs, databases, and worker services together with Docker Compose for local deployment practice.",
        "type": "workshop",
        "utility": 0.62,
    },
    {
        "id": "ci-cd-basics",
        "title": "CI/CD Basics",
        "topic": "Deployment",
        "duration_hours": 6,
        "difficulty": 3,
        "prerequisites": ["git-foundations", "testing-debugging"],
        "description": "Run tests automatically, package builds, and understand simple deployment pipelines.",
        "type": "course",
        "utility": 0.66,
    },
    {
        "id": "cloud-api-deployment",
        "title": "Cloud API Deployment Workshop",
        "topic": "Deployment",
        "duration_hours": 8,
        "difficulty": 4,
        "prerequisites": ["deployment-fundamentals", "docker-basics", "fastapi-basics"],
        "description": "Deploy a containerized API with configuration, health checks, logs, and rollback awareness.",
        "type": "workshop",
        "utility": 0.78,
    },
    {
        "id": "model-serving-basics",
        "title": "Model Serving Basics",
        "topic": "Deployment",
        "duration_hours": 7,
        "difficulty": 4,
        "prerequisites": ["machine-learning-intro", "fastapi-basics"],
        "description": "Expose a trained model behind an API and reason about serialization, latency, and versioning.",
        "type": "course",
        "utility": 0.74,
    },
    {
        "id": "mlops-monitoring-lab",
        "title": "MLOps Monitoring Lab",
        "topic": "Deployment",
        "duration_hours": 8,
        "difficulty": 5,
        "prerequisites": ["model-serving-basics", "model-evaluation"],
        "description": "Monitor predictions, errors, drift signals, and operational metrics for deployed ML services.",
        "type": "workshop",
        "utility": 0.8,
    },
    {
        "id": "deploy-rag-chatbot-project",
        "title": "Project: Deploy a RAG Chatbot",
        "topic": "Deployment",
        "duration_hours": 14,
        "difficulty": 5,
        "prerequisites": [
            "chatbot-deployment",
            "rag-chatbot-project",
            "docker-compose-workshop"
        ],
        "description": "Deploy a document-grounded chatbot with containers, configuration, logs, and release checks.",
        "type": "project",
        "utility": 0.94,
    },
    {
        "id": "bias-fairness-reading",
        "title": "Bias and Fairness Reading",
        "topic": "Responsible AI",
        "duration_hours": 3,
        "difficulty": 3,
        "prerequisites": ["ai-ethics-basics"],
        "description": "Review common bias sources, fairness trade-offs, and limits of purely technical mitigation.",
        "type": "reading",
        "utility": 0.44,
    },
    {
        "id": "ai-risk-assessment-workshop",
        "title": "AI Risk Assessment Workshop",
        "topic": "Responsible AI",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["ai-ethics-basics", "llm-fundamentals"],
        "description": "Identify misuse, hallucination, privacy, reliability, and user harm risks for an AI feature.",
        "type": "workshop",
        "utility": 0.63,
    },
    {
        "id": "privacy-threat-modeling",
        "title": "Privacy Threat Modeling",
        "topic": "Privacy",
        "duration_hours": 5,
        "difficulty": 4,
        "prerequisites": ["privacy-and-data-handling"],
        "description": "Map sensitive data flows, storage points, logging risks, access controls, and deletion needs.",
        "type": "workshop",
        "utility": 0.61,
    },
    {
        "id": "pii-redaction-lab",
        "title": "PII Redaction Lab",
        "topic": "Privacy",
        "duration_hours": 6,
        "difficulty": 4,
        "prerequisites": ["privacy-and-data-handling", "text-preprocessing"],
        "description": "Detect and redact personally identifiable information before indexing, logging, or sending to APIs.",
        "type": "workshop",
        "utility": 0.68,
    },
    {
        "id": "responsible-prompting-guide",
        "title": "Responsible Prompting Guide",
        "topic": "Responsible AI",
        "duration_hours": 4,
        "difficulty": 3,
        "prerequisites": ["prompt-engineering", "ai-ethics-basics"],
        "description": "Design prompts that clarify uncertainty, avoid unsafe claims, and route sensitive requests carefully.",
        "type": "reading",
        "utility": 0.55,
    },
    {
        "id": "ai-safety-evaluation-project",
        "title": "Project: AI Safety Evaluation",
        "topic": "Responsible AI",
        "duration_hours": 11,
        "difficulty": 5,
        "prerequisites": ["llm-evaluation-basics", "ai-risk-assessment-workshop"],
        "description": "Create an evaluation suite for harmful outputs, privacy failures, hallucinations, and escalation behavior.",
        "type": "project",
        "utility": 0.86,
    },
    {
        "id": "privacy-review-rag-project",
        "title": "Project: Privacy Review for RAG",
        "topic": "Privacy",
        "duration_hours": 10,
        "difficulty": 5,
        "prerequisites": ["rag-security-privacy", "privacy-threat-modeling"],
        "description": "Audit a RAG design for data exposure, permissions, retention, logging, and user-facing disclosures.",
        "type": "project",
        "utility": 0.82,
    },
]


def load_resource_dicts(input_path: str | Path) -> list[dict[str, Any]]:
    path = Path(input_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            resources = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Resources file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc.msg}") from exc

    if not isinstance(resources, list):
        raise ValueError(f"Expected {path} to contain a JSON list.")

    for index, resource in enumerate(resources):
        if not isinstance(resource, dict):
            raise ValueError(f"Expected resource {index} in {path} to be an object.")

    return resources


def validate_resources(resources: list[dict[str, Any]]) -> None:
    ids: list[str] = []

    for index, resource in enumerate(resources):
        missing_fields = REQUIRED_FIELDS - set(resource)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Resource at index {index} is missing fields: {missing}")

        resource_id = resource["id"]
        if not isinstance(resource_id, str) or not resource_id:
            raise ValueError(f"Resource at index {index} has an invalid id.")
        if not isinstance(resource["prerequisites"], list):
            raise ValueError(f"Resource {resource_id} prerequisites must be a list.")
        ids.append(resource_id)

    duplicate_ids = sorted({resource_id for resource_id in ids if ids.count(resource_id) > 1})
    if duplicate_ids:
        raise ValueError(f"Duplicate resource ids found: {', '.join(duplicate_ids)}")

    id_set = set(ids)
    for resource in resources:
        unknown_prerequisites = sorted(
            prerequisite
            for prerequisite in resource["prerequisites"]
            if prerequisite not in id_set
        )
        if unknown_prerequisites:
            unknown = ", ".join(unknown_prerequisites)
            raise ValueError(f"Resource {resource['id']} has unknown prerequisites: {unknown}")


def expand_resources(original_resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded_resources = [
        {**resource, "prerequisites": list(resource["prerequisites"])}
        for resource in original_resources
    ]
    expanded_resources.extend(
        {**resource, "prerequisites": list(resource["prerequisites"])}
        for resource in NEW_RESOURCES
    )
    validate_resources(expanded_resources)
    return expanded_resources


def save_resources(resources: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(resources, file, indent=2, ensure_ascii=False)
        file.write("\n")


def expand_resource_dataset(input_path: str | Path, output_path: str | Path) -> list[dict[str, Any]]:
    original_resources = load_resource_dicts(input_path)
    validate_resources(original_resources)
    expanded_resources = expand_resources(original_resources)
    save_resources(expanded_resources, output_path)
    return expanded_resources


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Expand the learning resources dataset with manually curated alternatives."
    )
    parser.add_argument(
        "--input",
        default="data/resources.json",
        help="Path to the original resources JSON file.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/resources_expanded.json",
        help="Path where the expanded resources JSON file will be written.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    expand_resource_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
