import type {
  ChatAskRequest,
  ChatAskResponse,
  GeneratePathRequest,
  GeneratePathResponse,
  Resource,
  ResourceUpdate,
  Student,
  StudentUpdate,
} from "./types";

const API_BASE_URL = "/api";

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers();
  const init: RequestInit = {
    method: options.method ?? "GET",
    headers,
  };

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    init.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    const message = await getErrorMessage(response);
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

async function getErrorMessage(response: Response): Promise<string> {
  const fallback = `Error ${response.status}: ${response.statusText || "respuesta no válida"}`;

  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (payload.detail) {
      return formatDetail(payload.detail);
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }

        return JSON.stringify(item);
      })
      .join("; ");
  }

  return JSON.stringify(detail);
}

export function getStudents(): Promise<Student[]> {
  return request<Student[]>("/students");
}

export function createStudent(student: Student): Promise<Student> {
  return request<Student>("/students", { method: "POST", body: student });
}

export function updateStudent(id: string, updates: StudentUpdate): Promise<Student> {
  return request<Student>(`/students/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: updates,
  });
}

export function deleteStudent(id: string): Promise<void> {
  return request<void>(`/students/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function getResources(): Promise<Resource[]> {
  return request<Resource[]>("/resources");
}

export function createResource(resource: Resource): Promise<Resource> {
  return request<Resource>("/resources", { method: "POST", body: resource });
}

export function updateResource(id: string, updates: ResourceUpdate): Promise<Resource> {
  return request<Resource>(`/resources/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: updates,
  });
}

export function deleteResource(id: string): Promise<void> {
  return request<void>(`/resources/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function generatePath(
  payload: GeneratePathRequest,
): Promise<GeneratePathResponse> {
  return request<GeneratePathResponse>("/paths/generate", {
    method: "POST",
    body: payload,
  });
}

export function askChat(payload: ChatAskRequest): Promise<ChatAskResponse> {
  return request<ChatAskResponse>("/chat/ask", { method: "POST", body: payload });
}
