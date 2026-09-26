import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Check, CornerDownLeft, Crosshair, Loader2, RotateCcw, Sparkles } from "lucide-react";
import { MAX_QUESTION_LENGTH, type ChatStatus } from "@/lib/api/careerGraphApi";
import { cn } from "@/lib/utils";
import { RichText } from "./RichText";
import { suggestedQuestions } from "./suggestions";
import { PIPELINE, type BackendState, type ChatMessage } from "./useCareerChat";

const statusMeta: Record<ChatStatus, { label: string; className: string }> = {
  answered: { label: "answered from graph", className: "text-brand border-brand/40" },
  no_results: { label: "no match in graph", className: "text-amber-300 border-amber-300/40" },
  off_topic: { label: "off topic", className: "text-neutral-400 border-white/15" },
  refused: { label: "blocked by guard", className: "text-rose-300 border-rose-300/40" },
  failed: { label: "query failed", className: "text-rose-300 border-rose-300/40" },
};

const backendMeta: Record<BackendState, { label: string; dot: string }> = {
  ready: { label: "online", dot: "bg-brand" },
  waking: { label: "waking up", dot: "bg-amber-400 animate-pulse" },
  offline: { label: "offline", dot: "bg-neutral-600" },
};

interface CareerChatProps {
  messages: ChatMessage[];
  pending: boolean;
  stage: number;
  backend: BackendState;
  focusedId: string | null;
  onAsk: (question: string) => void;
  onFocus: (message: ChatMessage) => void;
  onReset: () => void;
}

function Pipeline({ stage }: { stage: number }) {
  return (
    <ol className="space-y-1.5 font-mono text-xs">
      {PIPELINE.map((step, i) => (
        <li key={step} className={cn("flex items-center gap-2", i > stage ? "text-neutral-600" : "text-neutral-300")}>
          {i < stage ? (
            <Check className="h-3.5 w-3.5 text-brand" />
          ) : i === stage ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-brand" />
          ) : (
            <span className="h-3.5 w-3.5 text-center">·</span>
          )}
          {step}
        </li>
      ))}
    </ol>
  );
}

function AssistantMessage({ message, focused, onFocus }: { message: ChatMessage; focused: boolean; onFocus: () => void }) {
  if (message.error) {
    const busy = message.error.code === "llm_busy" || message.error.code === "rate_limited";
    return (
      <div className="flex gap-2.5 rounded-xl border border-amber-400/25 bg-amber-400/[0.06] p-3.5 text-sm text-amber-100">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
        <div>
          <p>{message.text}</p>
          {busy && message.error.retryAfterSeconds && (
            <p className="mt-1 font-mono text-xs text-amber-300/80">retry in ~{message.error.retryAfterSeconds}s</p>
          )}
        </div>
      </div>
    );
  }

  const meta = message.status ? statusMeta[message.status] : null;
  const nodeCount = message.nodeIds?.length ?? 0;
  return (
    <div
      className={cn(
        "rounded-xl border bg-white/[0.025] p-4 text-sm text-neutral-200 transition-colors",
        focused ? "border-brand/50" : "border-white/10",
      )}
    >
      {meta && (
        <span className={cn("mb-2.5 inline-block rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider", meta.className)}>
          {meta.label}
        </span>
      )}
      <RichText text={message.text} />
      {(message.cypher || nodeCount > 0) && (
        <div className="mt-3 space-y-2 border-t border-white/5 pt-3">
          {nodeCount > 0 && (
            <button
              type="button"
              onClick={onFocus}
              className={cn(
                "inline-flex items-center gap-1.5 font-mono text-xs transition-colors",
                focused ? "text-brand" : "text-neutral-400 hover:text-brand",
              )}
            >
              <Crosshair className="h-3.5 w-3.5" />
              {focused ? "Highlighted" : "Highlight"} {nodeCount} nodes in the graph
            </button>
          )}
          {message.cypher && (
            <details className="group">
              <summary className="cursor-pointer list-none font-mono text-xs text-neutral-500 hover:text-neutral-300">
                <span className="group-open:hidden">▸ show the Cypher it ran</span>
                <span className="hidden group-open:inline">▾ Cypher query (read-only, guarded)</span>
              </summary>
              <pre className="mt-2 overflow-x-auto rounded-lg border border-white/5 bg-black p-3 font-mono text-[11px] leading-relaxed text-brand/90">
                {message.cypher}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

export function CareerChat({ messages, pending, stage, backend, focusedId, onAsk, onFocus, onReset }: CareerChatProps) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const status = backendMeta[backend];
  const offline = backend === "offline";

  useEffect(() => {
    // Only follow the conversation once it exists; keep the intro visible on an empty chat.
    if (messages.length === 0) return;
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending, stage]);

  const submit = (question = draft) => {
    if (!question.trim() || pending || offline) return;
    onAsk(question.slice(0, MAX_QUESTION_LENGTH));
    setDraft("");
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#070707] shadow-[0_0_60px_-20px_hsl(var(--brand)/0.25)]">
      {/* Window chrome */}
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          </span>
          <span className="font-mono text-xs text-neutral-400">ask ~/career-graph</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-mono text-[11px] text-neutral-400">
            <span className={cn("h-1.5 w-1.5 rounded-full", status.dot)} />
            {status.label}
          </span>
          {messages.length > 0 && (
            <button type="button" onClick={onReset} aria-label="Clear conversation" className="text-neutral-500 hover:text-white">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Transcript */}
      <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-5" aria-live="polite">
        {messages.length === 0 && (
          <div className="space-y-5">
            <div>
              <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.25em] text-brand">
                <Sparkles className="h-3.5 w-3.5" /> GraphRAG over my career
              </p>
              <p className="mt-3 text-sm leading-relaxed text-neutral-300">
                Ask about my roles, projects, clients or skills. Your question becomes a Cypher query, a guard makes sure
                it's read-only, Neo4j runs it, and the answer is written only from what comes back. The nodes it used light
                up on the graph.
              </p>
              {offline && (
                <p className="mt-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 text-xs text-neutral-400">
                  The chat backend isn't connected in this build, but you can still explore the graph: drag, zoom and click
                  any node.
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={offline}
                  onClick={() => submit(q)}
                  className="rounded-full border border-white/10 px-3 py-1.5 text-left text-xs text-neutral-300 transition-colors hover:border-brand/50 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <p key={m.id} className="font-mono text-sm text-white">
              <span className="mr-2 text-brand">›</span>
              {m.text}
            </p>
          ) : (
            <AssistantMessage key={m.id} message={m} focused={focusedId === m.id} onFocus={() => onFocus(m)} />
          ),
        )}

        {pending && (
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <Pipeline stage={stage} />
          </div>
        )}
      </div>

      {/* Composer */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="border-t border-white/10 p-3"
      >
        <div className="flex items-end gap-2 rounded-xl border border-white/10 bg-black px-3 py-2 focus-within:border-brand/50">
          <span className="pb-1.5 font-mono text-sm text-brand">›</span>
          <textarea
            ref={inputRef}
            value={draft}
            rows={1}
            maxLength={MAX_QUESTION_LENGTH}
            disabled={offline}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={offline ? "Chat unavailable in this build" : "Ask my career graph…"}
            aria-label="Ask a question about Sanchit's career"
            className="max-h-32 min-h-[28px] flex-1 resize-none bg-transparent py-1 font-mono text-sm text-white placeholder:text-neutral-600 focus:outline-none disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!draft.trim() || pending || offline}
            aria-label="Send"
            className="mb-0.5 rounded-lg bg-brand p-1.5 text-brand-foreground transition-opacity disabled:opacity-30"
          >
            {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <CornerDownLeft className="h-4 w-4" />}
          </button>
        </div>
        <p className="mt-1.5 flex justify-between px-1 font-mono text-[10px] text-neutral-600">
          <span>enter to send · shift+enter for a new line</span>
          <span>
            {draft.length}/{MAX_QUESTION_LENGTH}
          </span>
        </p>
      </form>
    </div>
  );
}
