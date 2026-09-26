import { Link } from "react-router-dom";

const NotFound = () => (
  <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
    <p className="font-display text-8xl font-bold tracking-tighter text-brand">404</p>
    <p className="font-mono text-sm text-muted-foreground">MATCH (page) RETURN page → 0 rows</p>
    <Link to="/" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold hover:border-white/40">
      Back home
    </Link>
  </div>
);

export default NotFound;
