import { useEffect, useState, type FormEvent } from "react";
import {
  createResource,
  deleteResource,
  getResources,
  updateResource,
} from "../api/client";
import type { Resource, ResourceUpdate } from "../api/types";

type ResourceForm = {
  id: string;
  title: string;
  topic: string;
  duration_hours: number;
  difficulty: number;
  prerequisites: string;
  description: string;
  type: string;
  utility: number;
};

const emptyForm: ResourceForm = {
  id: "",
  title: "",
  topic: "",
  duration_hours: 1,
  difficulty: 3,
  prerequisites: "",
  description: "",
  type: "",
  utility: 1,
};

function ResourceManager() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [form, setForm] = useState<ResourceForm>(emptyForm);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    void loadResources();
  }, []);

  async function loadResources() {
    setLoading(true);
    setError("");

    try {
      setResources(await getResources());
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
      const payload = buildResourcePayload(form);
      if (editingId) {
        const updates: ResourceUpdate = {
          title: payload.title,
          topic: payload.topic,
          duration_hours: payload.duration_hours,
          difficulty: payload.difficulty,
          prerequisites: payload.prerequisites,
          description: payload.description,
          type: payload.type,
          utility: payload.utility,
        };
        await updateResource(editingId, updates);
        setSuccess("Recurso actualizado correctamente.");
      } else {
        await createResource(payload);
        setSuccess("Recurso creado correctamente.");
      }

      setForm(emptyForm);
      setEditingId(null);
      await loadResources();
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
      await deleteResource(id);
      setSuccess("Recurso eliminado correctamente.");
      if (editingId === id) {
        setEditingId(null);
        setForm(emptyForm);
      }
      await loadResources();
    } catch (err) {
      setError(getMessage(err));
    }
  }

  function startEdit(resource: Resource) {
    setEditingId(resource.id);
    setForm({
      id: resource.id,
      title: resource.title,
      topic: resource.topic,
      duration_hours: resource.duration_hours,
      difficulty: resource.difficulty,
      prerequisites: resource.prerequisites.join(", "),
      description: resource.description,
      type: resource.type,
      utility: resource.utility,
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
          <h2>Recursos</h2>
          <p>Administra el catalogo usado por el algoritmo greedy.</p>
        </div>
      </div>

      <form className="card form-grid" onSubmit={handleSubmit}>
        <div className="form-header">
          <h3>{editingId ? "Editar recurso" : "Crear recurso"}</h3>
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
          Titulo
          <input
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            required
          />
        </label>

        <label>
          Tema
          <input
            value={form.topic}
            onChange={(event) => setForm({ ...form, topic: event.target.value })}
            required
          />
        </label>

        <label>
          Duracion horas
          <input
            min={1}
            type="number"
            value={form.duration_hours}
            onChange={(event) =>
              setForm({ ...form, duration_hours: Number(event.target.value) })
            }
            required
          />
        </label>

        <label>
          Dificultad
          <select
            value={form.difficulty}
            onChange={(event) =>
              setForm({ ...form, difficulty: Number(event.target.value) })
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
          Tipo
          <input
            value={form.type}
            onChange={(event) => setForm({ ...form, type: event.target.value })}
            required
          />
        </label>

        <label>
          Utilidad
          <input
            step="0.01"
            type="number"
            value={form.utility}
            onChange={(event) =>
              setForm({ ...form, utility: Number(event.target.value) })
            }
            required
          />
        </label>

        <label className="full-width">
          Prerrequisitos
          <textarea
            value={form.prerequisites}
            onChange={(event) =>
              setForm({ ...form, prerequisites: event.target.value })
            }
            placeholder="python-basics, git-intro"
          />
        </label>

        <label className="full-width">
          Descripcion
          <textarea
            value={form.description}
            onChange={(event) =>
              setForm({ ...form, description: event.target.value })
            }
            required
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
        <p className="muted">Cargando recursos...</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Titulo</th>
                <th>Tema</th>
                <th>Horas</th>
                <th>Dificultad</th>
                <th>Prerrequisitos</th>
                <th>Tipo</th>
                <th>Descripcion</th>
                <th>Utilidad</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {resources.map((resource) => (
                <tr key={resource.id}>
                  <td>{resource.id}</td>
                  <td>{resource.title}</td>
                  <td>{resource.topic}</td>
                  <td>{resource.duration_hours}</td>
                  <td>{resource.difficulty}</td>
                  <td>{resource.prerequisites.join(", ") || "-"}</td>
                  <td>{resource.type}</td>
                  <td>{resource.description}</td>
                  <td>{resource.utility}</td>
                  <td className="row-actions">
                    <button
                      className="secondary"
                      type="button"
                      onClick={() => startEdit(resource)}
                    >
                      Editar
                    </button>
                    <button
                      className="danger"
                      type="button"
                      onClick={() => void handleDelete(resource.id)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
              {resources.length === 0 && (
                <tr>
                  <td colSpan={10}>No hay recursos registrados.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function buildResourcePayload(form: ResourceForm): Resource {
  return {
    id: form.id.trim(),
    title: form.title.trim(),
    topic: form.topic.trim(),
    duration_hours: Number(form.duration_hours),
    difficulty: Number(form.difficulty),
    prerequisites: splitCommaList(form.prerequisites),
    description: form.description.trim(),
    type: form.type.trim(),
    utility: Number(form.utility),
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

export default ResourceManager;
