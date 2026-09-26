/**
 * Client for the Career Graph API (backend/). Types mirror backend/app/api/schemas.py;
 * keep them in sync with the v1 contract documented in backend/README.md.
 */

export type ChatStatus = "answered" | "no_results" | "off_topic" | "refused" | "failed";

export interface ApiNode {
  id: string;
  label: string;
  name: string;
  properties: Record<string, unknown>;
}

export interface ApiEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

export interface ChatResponse {
  status: ChatStatus;
  answer: string;
  cypher: string | null;
  nodes: ApiNode[];
  edges: ApiEdge[];
}

export type ApiErrorCode =
  | "invalid_request"
  | "rate_limited"
  | "llm_busy"
  | "llm_unavailable"
  | "graph_unavailable"
  | "not_configured"
  | "network"
  | string;

export class CareerGraphApiError extends Error {
  constructor(
    readonly code: ApiErrorCode,
    message: string,
    readonly retryAfterSeconds?: number,
  ) {
    super(message);
    this.name = "CareerGraphApiError";
  }
}

export const MAX_QUESTION_LENGTH = 300;

const BASE_URL = (import.meta.env.VITE_CAREER_GRAPH_API_URL as string | undefined)?.replace(/\/$/, "");

export const isApiConfigured = Boolean(BASE_URL);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE_URL) {
    throw new CareerGraphApiError("not_configured", "The chat backend isn't connected yet.");
  }
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new CareerGraphApiError("network", "Couldn't reach the career graph. It may still be waking up.");
  }
  if (response.ok) return (await response.json()) as T;

  const retryAfter = Number(response.headers.get("Retry-After")) || undefined;
  let code: ApiErrorCode = `http_${response.status}`;
  let message = `Request failed (${response.status}).`;
  try {
    const body = await response.json();
    code = body?.error?.code ?? code;
    message = body?.error?.message ?? message;
  } catch {
    /* non-JSON error body; keep the defaults */
  }
  throw new CareerGraphApiError(code, message, retryAfter);
}

export const careerGraphApi = {
  /** Cheap liveness ping; also wakes a sleeping free-tier instance. */
  health: () => request<{ status: "ok" }>("/health"),
  ask: (question: string) =>
    request<ChatResponse>("/api/v1/chat", { method: "POST", body: JSON.stringify({ question }) }),
};
