import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Maximize2, MessageSquarePlus, X } from "lucide-react";
import { SiteNav } from "@/components/layout/SiteNav";
import { KnowledgeGraph, type GraphHighlight, type GraphNode, type KnowledgeGraphHandle } from "@/components/ui/knowledge-graph";
import { graphStats, type GraphNodeRecord } from "@/data/careerGraph";
import { CareerChat } from "@/features/career-chat/CareerChat";
import { graphLegend, graphLinks, graphNodes } from "@/features/career-chat/graphModel";
import { useCareerChat, type ChatMessage } from "@/features/career-chat/useCareerChat";

const HIDDEN_PROPS = new Set(["label", "id", "name"]);

function NodeCard({ node, onAsk, onClose }: { node: GraphNode; onAsk: (q: string) => void; onClose: () => void }) {
  const record = node.data as GraphNodeRecord;
  const props = Object.entries(record).filter(([k, v]) => !HIDDEN_PROPS.has(k) && v !== undefined && v !== "");
  const question = node.type === "Skill" ? `What has Sanchit built with ${node.label}?` : `Tell me about ${node.label}`;

  return (
    <div className="absolute right-3 top-3 z-20 w-[min(22rem,calc(100%-1.5rem))] rounded-xl border border-white/10 bg-black/85 p-4 shadow-2xl backdrop-blur-md animate-fade-in">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest" style={{ color: node.color }}>
            {node.type}
          </p>
          <h3 className="mt-1 font-display text-lg font-bold leading-tight">{node.label}</h3>
        </div>
        <button type="button" onClick={onClose} aria-label="Close" className="text-neutral-500 hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>
      {props.length > 0 && (
        <dl className="mt-3 max-h-40 space-y-1.5 overflow-y-auto text-xs">
          {props.map(([key, value]) => (
            <div key={key}>
              <dt className="font-mono text-neutral-500">{key.replace(/_/g, " ")}</dt>
              <dd className="break-words text-neutral-300">{String(value)}</dd>
            </div>
          ))}
        </dl>
      )}
      <button
        type="button"
        onClick={() => onAsk(question)}
        className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-brand/40 px-3 py-1.5 font-mono text-xs text-brand hover:bg-brand hover:text-brand-foreground"
      >
        <MessageSquarePlus className="h-3.5 w-3.5" /> Ask about this
      </button>
    </div>
  );
}

export default function CareerGraph() {
  const chat = useCareerChat();
  const graphRef = useRef<KnowledgeGraphHandle>(null);
  const [focused, setFocused] = useState<ChatMessage | null>(null);
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [params, setParams] = useSearchParams();
  const askedFromUrl = useRef(false);

  // Follow the newest answer that touched the graph.
  useEffect(() => {
    const latest = [...chat.messages].reverse().find((m) => m.role === "assistant" && m.nodeIds?.length);
    setFocused(latest ?? null);
  }, [chat.messages]);

  // /graph?q=... asks once the page opens (links from the homepage).
  useEffect(() => {
    const q = params.get("q");
    if (q && !askedFromUrl.current && chat.backend !== "offline") {
      askedFromUrl.current = true;
      chat.ask(q);
      setParams({}, { replace: true });
    }
  }, [params, chat, setParams]);

  const highlight = useMemo<GraphHighlight | null>(
    () => (focused ? { nodeIds: new Set(focused.nodeIds), edgeIds: new Set(focused.edgeIds) } : null),
    [focused],
  );

  const askAbout = (question: string) => {
    setSelected(null);
    chat.ask(question);
  };

  return (
    <div className="flex h-[100svh] flex-col bg-background">
      <SiteNav />
      <main className="grid min-h-0 flex-1 gap-3 p-3 pt-[4.5rem] lg:grid-cols-[minmax(0,1fr)_440px]">
        <section className="relative min-h-[45svh] overflow-hidden rounded-2xl border border-white/10 bg-[#050505] bg-grid">
          <div className="pointer-events-none absolute left-4 top-4 z-10">
            <h1 className="font-display text-xl font-bold tracking-tight sm:text-2xl">
              Sanchit's career <span className="text-brand">graph</span>
            </h1>
            <p className="mt-1 font-mono text-[11px] text-neutral-500">
              {graphStats.nodes} nodes · {graphStats.relationships} relationships · Neo4j
            </p>
          </div>
          <div className="absolute bottom-3 right-3 z-10 flex gap-2">
            {focused && (
              <button
                type="button"
                onClick={() => setFocused(null)}
                className="rounded-lg border border-white/10 bg-black/70 px-2.5 py-1.5 font-mono text-[11px] text-neutral-300 backdrop-blur-sm hover:text-white"
              >
                clear highlight
              </button>
            )}
            <button
              type="button"
              onClick={() => graphRef.current?.resetZoom()}
              aria-label="Fit graph to screen"
              className="rounded-lg border border-white/10 bg-black/70 p-1.5 text-neutral-300 backdrop-blur-sm hover:text-white"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>

          <KnowledgeGraph
            ref={graphRef}
            nodes={graphNodes}
            links={graphLinks}
            highlight={highlight}
            selectedId={selected?.id}
            onNodeClick={setSelected}
            legend={graphLegend}
          />
          {selected && <NodeCard node={selected} onAsk={askAbout} onClose={() => setSelected(null)} />}
        </section>

        <section className="min-h-[70svh] lg:min-h-0">
          <CareerChat
            messages={chat.messages}
            pending={chat.pending}
            stage={chat.stage}
            backend={chat.backend}
            focusedId={focused?.id ?? null}
            onAsk={chat.ask}
            onFocus={setFocused}
            onReset={() => {
              chat.reset();
              setFocused(null);
            }}
          />
        </section>
      </main>
    </div>
  );
}
