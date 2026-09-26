/** Chat state for the career-graph assistant: messages, the in-flight pipeline stage, and backend reachability. */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  CareerGraphApiError,
  careerGraphApi,
  isApiConfigured,
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
  /** True while the answer text is still streaming in. */
  streaming?: boolean;
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

      const answerId = nextId();
      const update = (patch: (m: ChatMessage) => Partial<ChatMessage>) =>
        setMessages((all) => all.map((m) => (m.id === answerId ? { ...m, ...patch(m) } : m)));

      try {
        const answer = await careerGraphApi.askStream(text, {
          // The query has run: show its status and highlight the graph while the answer is written.
          onMeta: (meta) => {
            window.clearInterval(stageTimer.current);
            setBackend("ready");
            setMessages((m) => [
              ...m,
              {
                id: answerId,
                role: "assistant",
                text: "",
                status: meta.status,
                cypher: meta.cypher,
                nodeIds: meta.nodes.map((n) => n.id),
                edgeIds: meta.edges.map((e) => e.id),
                streaming: true,
              },
            ]);
          },
          onDelta: (chunk) => update((m) => ({ text: m.text + chunk })),
        });
        update(() => ({ text: answer, streaming: false }));
      } catch (err) {
        const e = err instanceof CareerGraphApiError ? err : new CareerGraphApiError("unknown", "Something went wrong.");
        if (e.code === "not_configured") setBackend("offline");
        const error = { code: e.code, retryAfterSeconds: e.retryAfterSeconds };
        setMessages((m) =>
          // A failure mid-stream replaces the partial answer; otherwise it's a new message.
          m.some((x) => x.id === answerId)
            ? m.map((x) => (x.id === answerId ? { ...x, text: e.message, error, streaming: false } : x))
            : [...m, { id: answerId, role: "assistant", text: e.message, error }],
        );
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
