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

function requireBaseUrl(): string {
  if (!BASE_URL) {
    throw new CareerGraphApiError("not_configured", "The chat backend isn't connected yet.");
  }
  return BASE_URL;
}

async function send(path: string, init?: RequestInit): Promise<Response> {
  const base = requireBaseUrl();
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new CareerGraphApiError("network", "Couldn't reach the career graph. It may still be waking up.");
  }
  if (response.ok) return response;

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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return (await (await send(path, init)).json()) as T;
}

/** Everything in a ChatResponse except the answer text, which streams separately. */
export type ChatMeta = Omit<ChatResponse, "answer">;

export interface StreamHandlers {
  onMeta: (meta: ChatMeta) => void;
  onDelta: (text: string) => void;
}

/**
 * POST /api/v1/chat/stream and dispatch its server-sent events. Resolves with the full answer.
 * (EventSource can't POST, so the stream is read and parsed by hand.)
 */
async function askStream(question: string, handlers: StreamHandlers): Promise<string> {
  let response: Response;
  try {
    response = await send("/api/v1/chat/stream", { method: "POST", body: JSON.stringify({ question }) });
  } catch (err) {
    // A backend that predates streaming: answer in one go instead.
    if (err instanceof CareerGraphApiError && err.code === "not_found") {
      const { answer, ...meta } = await careerGraphApi.ask(question);
      handlers.onMeta(meta);
      return answer;
    }
    throw err;
  }
  if (!response.body) throw new CareerGraphApiError("network", "The answer stream was empty.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let answer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      const payload = JSON.parse(data);
      if (event === "meta") handlers.onMeta(payload as ChatMeta);
      else if (event === "delta") {
        answer += payload.text;
        handlers.onDelta(payload.text);
      } else if (event === "done") return payload.answer as string;
      else if (event === "error") throw new CareerGraphApiError(payload.code, payload.message);
    }
  }
  if (!answer) throw new CareerGraphApiError("network", "The answer was cut off. Please try again.");
  return answer;
}

export const careerGraphApi = {
  /** Cheap liveness ping; also wakes a sleeping free-tier instance. */
  health: () => request<{ status: "ok" }>("/health"),
  ask: (question: string) =>
    request<ChatResponse>("/api/v1/chat", { method: "POST", body: JSON.stringify({ question }) }),
  askStream,
};
