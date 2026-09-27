import { Link } from "react-router-dom";
import { profile } from "@/content/profile";

export default function Footer() {
  return (
    <footer className="border-t border-white/5 py-8">
      <div className="page-container flex flex-col items-center justify-between gap-3 font-mono text-xs text-muted-foreground sm:flex-row">
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
