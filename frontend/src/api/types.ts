export type Preference = "practical" | "theoretical" | "balanced";

export type Algorithm = "greedy";

export type Student = {
  id: string;
  goal: string;
  available_hours: number;
  known_resources: string[];
  preferred_difficulty: number;
  preference: Preference;
};

export type StudentUpdate = {
  goal?: string;
  available_hours?: number;
  known_resources?: string[];
  preferred_difficulty?: number;
  preference?: Preference;
};

export type Resource = {
  id: string;
  title: string;
  topic: string;
  duration_hours: number;
  difficulty: number;
  prerequisites: string[];
  description: string;
  type: string;
  utility: number;
};

export type ResourceUpdate = {
  title?: string;
  topic?: string;
  duration_hours?: number;
  difficulty?: number;
  prerequisites?: string[];
  description?: string;
  type?: string;
  utility?: number;
};

export type GeneratePathRequest = {
  student_id: string;
  algorithm: Algorithm;
  use_llm: boolean;
};

export type PathResource = Resource;

export type RouteValidation = {
  is_valid: boolean;
  violations: string[];
};

export type GeneratePathResponse = {
  student: Student;
  algorithm: string;
  path: PathResource[];
  metrics: Record<string, unknown>;
  validation: RouteValidation;
};

export type ChatAskRequest = {
  message: string;
  algorithm: Algorithm;
};

export type ChatAskResponse = {
  interpreted_profile: Record<string, unknown>;
  generated_student: Student;
  algorithm: string;
  path: PathResource[];
  metrics: Record<string, unknown>;
  validation: RouteValidation;
};
