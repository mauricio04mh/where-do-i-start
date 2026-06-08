import { useState, type FormEvent } from "react";
import { askChat } from "../api/client";
import type { Algorithm, ChatAskResponse } from "../api/types";
import PathResult from "./PathResult";

const samplePrompt =
  "Quiero aprender a crear un chatbot con RAG, se Python y tengo 30 horas.";

function ChatPathGenerator() {
  const [message, setMessage] = useState(samplePrompt);
  const [algorithm, setAlgorithm] = useState<Algorithm>("greedy");
  const [useLlm, setUseLlm] = useState(false);
  const [result, setResult] = useState<ChatAskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      setResult(await askChat({ message, algorithm, use_llm: useLlm }));
    } catch (err) {
      setError(getMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h2>Preguntar</h2>
          <p>Interpreta una solicitud en lenguaje natural y genera una ruta.</p>
        </div>
      </div>

      <p className="message warning">
        Este endpoint requiere GEMINI_API_KEY configurado en el backend.
      </p>

      <form className="card form-grid compact" onSubmit={handleAsk}>
        <label className="full-width">
          Pregunta
          <textarea
            className="large-textarea"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            required
          />
        </label>

        <label>
          Algoritmo
          <select
            value={algorithm}
            onChange={(event) => setAlgorithm(event.target.value as Algorithm)}
          >
            <option value="greedy">greedy</option>
            <option value="branch_and_bound">branch_and_bound</option>
            <option value="simulated_annealing">simulated_annealing</option>
          </select>
        </label>

        <label className="check-row full-width">
          <input
            checked={useLlm}
            type="checkbox"
            onChange={(event) => setUseLlm(event.target.checked)}
          />
          <span>
            Usar LLM para reordenar los mejores candidatos por relevancia semantica.
          </span>
        </label>

        <div className="form-actions">
          <button disabled={loading || !message.trim()} type="submit">
            {loading ? "Generando..." : "Preguntar y generar ruta"}
          </button>
        </div>
      </form>

      {error && <p className="message error">{error}</p>}

      {result && (
        <>
          <section className="block">
            <h3>Perfil interpretado</h3>
            <pre className="json-box">
              {JSON.stringify(result.interpreted_profile, null, 2)}
            </pre>
          </section>

          <section className="block">
            <h3>Estudiante generado</h3>
            <div className="summary-grid">
              <div className="summary-item">
                <span>ID</span>
                <strong>{result.generated_student.id}</strong>
              </div>
              <div className="summary-item">
                <span>Objetivo</span>
                <strong>{result.generated_student.goal}</strong>
              </div>
              <div className="summary-item">
                <span>Horas</span>
                <strong>{result.generated_student.available_hours}</strong>
              </div>
              <div className="summary-item">
                <span>Preferencia</span>
                <strong>{result.generated_student.preference}</strong>
              </div>
            </div>
          </section>

          <PathResult
            result={{
              student: result.generated_student,
              algorithm: result.algorithm,
              path: result.path,
              metrics: result.metrics,
              validation: result.validation,
              llm_debug: result.llm_debug,
            }}
          />
        </>
      )}
    </section>
  );
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrio un error inesperado.";
}

export default ChatPathGenerator;
