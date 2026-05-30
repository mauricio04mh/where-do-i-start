import { useEffect, useState, type FormEvent } from "react";
import {
  createStudent,
  deleteStudent,
  getStudents,
  updateStudent,
} from "../api/client";
import type { Preference, Student, StudentUpdate } from "../api/types";

type StudentForm = {
  id: string;
  goal: string;
  available_hours: number;
  known_resources: string;
  preferred_difficulty: number;
  preference: Preference;
  target_topics: string;
  constraints: string;
};

const emptyForm: StudentForm = {
  id: "",
  goal: "",
  available_hours: 10,
  known_resources: "",
  preferred_difficulty: 3,
  preference: "balanced",
  target_topics: "",
  constraints: "",
};

function StudentManager() {
  const [students, setStudents] = useState<Student[]>([]);
  const [form, setForm] = useState<StudentForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    void loadStudents();
  }, []);

  async function loadStudents() {
    setLoading(true);
    setError("");

    try {
      setStudents(await getStudents());
    } catch (err) {
      setError(getMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload = buildStudentPayload(form);
      if (editingId) {
        const updates: StudentUpdate = {
          goal: payload.goal,
          available_hours: payload.available_hours,
          known_resources: payload.known_resources,
          preferred_difficulty: payload.preferred_difficulty,
          preference: payload.preference,
          target_topics: payload.target_topics,
          constraints: payload.constraints,
        };
        await updateStudent(editingId, updates);
        setSuccess("Estudiante actualizado correctamente.");
      } else {
        await createStudent(payload);
        setSuccess("Estudiante creado correctamente.");
      }

      setForm(emptyForm);
      setEditingId(null);
      await loadStudents();
    } catch (err) {
      setError(getMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string) {
    setError("");
    setSuccess("");

    try {
      await deleteStudent(id);
      setSuccess("Estudiante eliminado correctamente.");
      if (editingId === id) {
        setEditingId(null);
        setForm(emptyForm);
      }
      await loadStudents();
    } catch (err) {
      setError(getMessage(err));
    }
  }

  function startEdit(student: Student) {
    setEditingId(student.id);
    setForm({
      id: student.id,
      goal: student.goal,
      available_hours: student.available_hours,
      known_resources: student.known_resources.join(", "),
      preferred_difficulty: student.preferred_difficulty,
      preference: student.preference,
      target_topics: student.target_topics.join(", "),
      constraints: student.constraints.join(", "),
    });
    setError("");
    setSuccess("");
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setSuccess("");
  }

  return (
    <section>
      <div className="section-heading">
        <div>
          <h2>Estudiantes</h2>
          <p>Gestiona los perfiles usados para generar rutas.</p>
        </div>
      </div>

      <form className="card form-grid" onSubmit={handleSubmit}>
        <div className="form-header">
          <h3>{editingId ? "Editar estudiante" : "Crear estudiante"}</h3>
          {editingId && (
            <button className="secondary" type="button" onClick={cancelEdit}>
              Cancelar
            </button>
          )}
        </div>

        <label>
          ID
          <input
            value={form.id}
            disabled={Boolean(editingId)}
            onChange={(event) => setForm({ ...form, id: event.target.value })}
            required
          />
        </label>

        <label>
          Objetivo
          <input
            value={form.goal}
            onChange={(event) => setForm({ ...form, goal: event.target.value })}
            required
          />
        </label>

        <label>
          Horas disponibles
          <input
            min={1}
            type="number"
            value={form.available_hours}
            onChange={(event) =>
              setForm({ ...form, available_hours: Number(event.target.value) })
            }
            required
          />
        </label>

        <label>
          Dificultad preferida
          <select
            value={form.preferred_difficulty}
            onChange={(event) =>
              setForm({ ...form, preferred_difficulty: Number(event.target.value) })
            }
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label>
          Preferencia
          <select
            value={form.preference}
            onChange={(event) =>
              setForm({ ...form, preference: event.target.value as Preference })
            }
          >
            <option value="practical">practical</option>
            <option value="theoretical">theoretical</option>
            <option value="balanced">balanced</option>
          </select>
        </label>

        <label className="full-width">
          Recursos conocidos
          <textarea
            value={form.known_resources}
            onChange={(event) =>
              setForm({ ...form, known_resources: event.target.value })
            }
            placeholder="python-basics, git-intro"
          />
        </label>

        <label className="full-width">
          Topicos objetivo
          <textarea
            value={form.target_topics}
            onChange={(event) =>
              setForm({ ...form, target_topics: event.target.value })
            }
            placeholder="Web Development, Backend Development, Databases"
          />
        </label>

        <label className="full-width">
          Restricciones
          <textarea
            value={form.constraints}
            onChange={(event) =>
              setForm({ ...form, constraints: event.target.value })
            }
            placeholder="sin conocimientos avanzados, proyectos practicos"
          />
        </label>

        <div className="form-actions">
          <button disabled={saving} type="submit">
            {saving ? "Guardando..." : editingId ? "Guardar cambios" : "Crear"}
          </button>
        </div>
      </form>

      <Messages error={error} success={success} />

      {loading ? (
        <p className="muted">Cargando estudiantes...</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Objetivo</th>
                <th>Horas</th>
                <th>Dificultad</th>
                <th>Preferencia</th>
                <th>Recursos conocidos</th>
                <th>Topicos objetivo</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {students.map((student) => (
                <tr key={student.id}>
                  <td>{student.id}</td>
                  <td>{student.goal}</td>
                  <td>{student.available_hours}</td>
                  <td>{student.preferred_difficulty}</td>
                  <td>{student.preference}</td>
                  <td>{student.known_resources.join(", ") || "-"}</td>
                  <td>{student.target_topics.join(", ") || "-"}</td>
                  <td className="row-actions">
                    <button
                      className="secondary"
                      type="button"
                      onClick={() => startEdit(student)}
                    >
                      Editar
                    </button>
                    <button
                      className="danger"
                      type="button"
                      onClick={() => void handleDelete(student.id)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {students.length === 0 && (
                <tr>
                  <td colSpan={8}>No hay estudiantes registrados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function buildStudentPayload(form: StudentForm): Student {
  return {
    id: form.id.trim(),
    goal: form.goal.trim(),
    available_hours: Number(form.available_hours),
    known_resources: splitCommaList(form.known_resources),
    preferred_difficulty: Number(form.preferred_difficulty),
    preference: form.preference,
    target_topics: splitCommaList(form.target_topics),
    constraints: splitCommaList(form.constraints),
  };
}

function splitCommaList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrio un error inesperado.";
}

function Messages({ error, success }: { error: string; success: string }) {
  return (
    <>
      {error && <p className="message error">{error}</p>}
      {success && <p className="message success">{success}</p>}
    </>
  );
}

export default StudentManager;
