import { Link } from "react-router-dom";
import { profile } from "@/content/profile";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 font-mono text-xs text-muted-foreground sm:flex-row sm:px-8">
        <p>
          © {new Date().getFullYear()} {profile.firstName} {profile.lastName} · {profile.location}
        </p>
        <p>
          Built with React, FastAPI, Neo4j &amp; Gemini ·{" "}
          <Link to="/graph" className="text-brand hover:underline">
            ask the graph
          </Link>
        </p>
      </div>
    </footer>
  );
}
