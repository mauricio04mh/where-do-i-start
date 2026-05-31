import { useEffect, useState, type FormEvent } from "react";
import { generatePath, getStudents } from "../api/client";
import type { Algorithm, GeneratePathResponse, Student } from "../api/types";
import PathResult from "./PathResult";

function PathGenerator() {
  const [students, setStudents] = useState<Student[]>([]);
  const [studentId, setStudentId] = useState("");
  const [algorithm, setAlgorithm] = useState<Algorithm>("greedy");
  const [useLlm, setUseLlm] = useState(false);
  const [result, setResult] = useState<GeneratePathResponse | null>(null);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadStudents() {
      setLoadingStudents(true);
      setError("");

      try {
        const loadedStudents = await getStudents();
        setStudents(loadedStudents);
        setStudentId((current) => current || loadedStudents[0]?.id || "");
      } catch (err) {
        setError(getMessage(err));
      } finally {
        setLoadingStudents(false);
      }
    }

    void loadStudents();
  }, []);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGenerating(true);
    setError("");
    setResult(null);

    try {
      setResult(
        await generatePath({
          student_id: studentId,
          algorithm,
          use_llm: useLlm,
        }),
      );
    } catch (err) {
      setError(getMessage(err));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h2>Generar ruta</h2>
          <p>Selecciona un estudiante y ejecuta un algoritmo de rutas.</p>
        </div>
      </div>

      <form className="card form-grid compact" onSubmit={handleGenerate}>
        <label>
          Estudiante
          <select
            value={studentId}
            onChange={(event) => setStudentId(event.target.value)}
            disabled={loadingStudents}
            required
          >
            {students.map((student) => (
              <option key={student.id} value={student.id}>
                {student.id} - {student.goal}
              </option>
            ))}
          </select>
        </label>

        <label>
          Algoritmo
          <select
            value={algorithm}
            onChange={(event) => setAlgorithm(event.target.value as Algorithm)}
          >
            <option value="greedy">greedy</option>
            <option value="backtracking">backtracking</option>
            <option value="branch_and_bound">branch_and_bound</option>
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
          <button disabled={generating || !studentId} type="submit">
            {generating ? "Generando..." : "Generar ruta"}
          </button>
        </div>
      </form>

      {error && <p className="message error">{error}</p>}
      {loadingStudents && <p className="muted">Cargando estudiantes...</p>}
      {!loadingStudents && students.length === 0 && (
        <p className="message warning">
          No hay estudiantes disponibles. Crea uno antes de generar rutas.
        </p>
      )}

      {result && <PathResult result={result} />}
    </section>
  );
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrio un error inesperado.";
}

export default PathGenerator;
