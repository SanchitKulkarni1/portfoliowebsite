/** Chat state for the career-graph assistant: messages, the in-flight pipeline stage, and backend reachability. */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  CareerGraphApiError,
  careerGraphApi,
  isApiConfigured,
  type ChatResponse,
  type ChatStatus,
} from "@/lib/api/careerGraphApi";

export type BackendState = "offline" | "waking" | "ready";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  status?: ChatStatus;
  cypher?: string | null;
  nodeIds?: string[];
  edgeIds?: string[];
  error?: { code: string; retryAfterSeconds?: number };
}

/** The steps the backend performs, shown while a question is in flight. */
export const PIPELINE = [
  "Reading the question",
  "Writing Cypher with Gemini",
  "Checking the query is read-only",
  "Querying Neo4j",
  "Writing an answer from the results",
] as const;

let counter = 0;
const nextId = () => `m${++counter}`;

export function useCareerChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [stage, setStage] = useState(0);
  const [backend, setBackend] = useState<BackendState>(isApiConfigured ? "waking" : "offline");
  const stageTimer = useRef<number>();

  // Wake the (possibly sleeping) free-tier backend as soon as the page opens.
  useEffect(() => {
    if (!isApiConfigured) return;
    let cancelled = false;
    careerGraphApi
      .health()
      .then(() => !cancelled && setBackend("ready"))
      .catch(() => !cancelled && setBackend("waking"));
    return () => {
      cancelled = true;
    };
  }, []);

  const ask = useCallback(
    async (question: string) => {
      const text = question.trim();
      if (!text || pending) return;
      setMessages((m) => [...m, { id: nextId(), role: "user", text }]);
      setPending(true);
      setStage(0);
      window.clearInterval(stageTimer.current);
      // Advance the visual pipeline; the last stage holds until the response arrives.
      stageTimer.current = window.setInterval(() => setStage((s) => Math.min(s + 1, PIPELINE.length - 1)), 650);

      try {
        const res: ChatResponse = await careerGraphApi.ask(text);
        setBackend("ready");
        setMessages((m) => [
          ...m,
          {
            id: nextId(),
            role: "assistant",
            text: res.answer,
            status: res.status,
            cypher: res.cypher,
            nodeIds: res.nodes.map((n) => n.id),
            edgeIds: res.edges.map((e) => e.id),
          },
        ]);
      } catch (err) {
        const e = err instanceof CareerGraphApiError ? err : new CareerGraphApiError("unknown", "Something went wrong.");
        if (e.code === "not_configured") setBackend("offline");
        setMessages((m) => [
          ...m,
          { id: nextId(), role: "assistant", text: e.message, error: { code: e.code, retryAfterSeconds: e.retryAfterSeconds } },
        ]);
      } finally {
        window.clearInterval(stageTimer.current);
        setPending(false);
      }
    },
    [pending],
  );

  useEffect(() => () => window.clearInterval(stageTimer.current), []);

  const reset = useCallback(() => setMessages([]), []);

  return { messages, pending, stage, backend, ask, reset };
}
