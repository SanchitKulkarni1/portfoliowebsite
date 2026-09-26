import { ArrowRight, Terminal } from "lucide-react";
import { Link } from "react-router-dom";
import { suggestedQuestions } from "@/features/career-chat/suggestions";
import { graphStats } from "@/data/careerGraph";
import { useReveal } from "@/hooks/useReveal";

/** Homepage section that invites visitors to the career-graph chat. */
export function AskTeaser() {
  const ref = useReveal<HTMLDivElement>();
  return (
    <section className="py-20">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <div
          ref={ref}
          className="reveal relative overflow-hidden rounded-3xl border border-brand/25 bg-gradient-to-br from-brand/[0.08] via-card to-card p-8 sm:p-12"
        >
          <div className="pointer-events-none absolute inset-0 bg-grid opacity-60 [mask-image:linear-gradient(to_left,black,transparent_70%)]" />
          <div className="relative grid gap-10 lg:grid-cols-[1.2fr_1fr] lg:items-center">
            <div>
              <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-[0.3em] text-brand">
                <Terminal className="h-4 w-4" /> Don't read it, query it
              </p>
              <h2 className="mt-4 font-display text-3xl font-bold leading-tight tracking-tight sm:text-5xl">
                Ask my career graph anything.
              </h2>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-neutral-300">
                Everything on this page is also a Neo4j knowledge graph ({graphStats.nodes} nodes, {graphStats.relationships}{" "}
                relationships). Ask a question in plain English: an LLM writes the Cypher, a guard checks it's read-only, and
                the answer comes straight from the graph.
              </p>
              <Link
                to="/graph"
                className="mt-8 inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 font-semibold text-brand-foreground transition-transform hover:scale-[1.03]"
              >
                Open the graph <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <ul className="space-y-2.5">
              {suggestedQuestions.slice(0, 4).map((question) => (
                <li key={question}>
                  <Link
                    to={`/graph?q=${encodeURIComponent(question)}`}
                    className="flex items-center justify-between gap-4 rounded-xl border border-white/10 bg-background/60 px-4 py-3 font-mono text-sm text-neutral-300 transition-colors hover:border-brand/50 hover:text-white"
                  >
                    <span>
                      <span className="text-brand">›</span> {question}
                    </span>
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
