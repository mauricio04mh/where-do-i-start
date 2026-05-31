import type { PathResource, Student, RouteValidation } from "../api/types";

export type PathResultData = {
  student: Student;
  algorithm: string;
  path: PathResource[];
  metrics: Record<string, unknown>;
  validation: RouteValidation;
  llm_debug?: Record<string, unknown> | null;
};

type PathResultProps = {
  result: PathResultData;
};

const importantMetricKeys = [
  "total_duration",
  "total_utility",
  "time_usage_ratio",
  "coverage_score",
  "resource_count",
];

function PathResult({ result }: PathResultProps) {
  const importantMetrics = importantMetricKeys.filter((key) => key in result.metrics);
  const metricEntries = Object.entries(result.metrics);

  return (
    <section className="result-section">
      <div className="section-heading">
        <div>
          <h2>Resultado</h2>
          <p>Algoritmo: {result.algorithm}</p>
        </div>
      </div>

      <div className="summary-grid">
        <div className="summary-item">
          <span>Estudiante</span>
          <strong>{result.student.id}</strong>
        </div>
        <div className="summary-item">
          <span>Objetivo</span>
          <strong>{result.student.goal}</strong>
        </div>
        <div className="summary-item">
          <span>Horas disponibles</span>
          <strong>{result.student.available_hours}</strong>
        </div>
        <div className="summary-item">
          <span>Preferencia</span>
          <strong>{result.student.preference}</strong>
        </div>
      </div>

      {importantMetrics.length > 0 && (
        <div className="metric-strip">
          {importantMetrics.map((key) => (
            <div key={key}>
              <span>{key}</span>
              <strong>{formatValue(result.metrics[key])}</strong>
            </div>
          ))}
        </div>
      )}

      <section className="block">
        <h3>Ruta ordenada</h3>
        {result.path.length === 0 ? (
          <p className="muted">No se generaron recursos para esta ruta.</p>
        ) : (
          <div className="path-list">
            {result.path.map((resource, index) => (
              <article className="path-card" key={`${resource.id}-${index}`}>
                <div className="path-position">{index + 1}</div>
                <div>
                  <h4>{resource.title}</h4>
                  <p className="muted">{resource.description}</p>
                  <div className="resource-meta">
                    <span>ID: {resource.id}</span>
                    <span>Tema: {resource.topic}</span>
                    <span>Duracion: {resource.duration_hours} h</span>
                    <span>Dificultad: {resource.difficulty}</span>
                    <span>Utilidad: {formatUtility(resource.utility)}</span>
                    <span>
                      Prerrequisitos:{" "}
                      {resource.prerequisites.length > 0
                        ? resource.prerequisites.join(", ")
                        : "ninguno"}
                    </span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="block">
        <h3>Metricas</h3>
        {metricEntries.length === 0 ? (
          <p className="muted">No hay metricas disponibles.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Metrica</th>
                  <th>Valor</th>
                </tr>
              </thead>
              <tbody>
                {metricEntries.map(([key, value]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{formatValue(value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="block">
        <h3>Validacion</h3>
        {result.validation.is_valid ? (
          <p className="success-inline">Ruta valida</p>
        ) : (
          <ul className="violations">
            {result.validation.violations.map((violation) => (
              <li key={violation}>{violation}</li>
            ))}
          </ul>
        )}
      </section>

      {result.llm_debug && (
        <section className="block">
          <details>
            <summary>LLM scoring debug</summary>
            <pre className="json-box">
              {JSON.stringify(result.llm_debug, null, 2)}
            </pre>
          </details>
        </section>
      )}
    </section>
  );
}

function formatUtility(value: unknown): string {
  return typeof value === "number" ? value.toFixed(2) : formatValue(value);
}

function formatValue(value: unknown): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }

  if (typeof value === "boolean") {
    return value ? "si" : "no";
  }

  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

export default PathResult;
