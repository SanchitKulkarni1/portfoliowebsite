import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Menu, Network, X } from "lucide-react";
import { profile } from "@/content/profile";
import { cn } from "@/lib/utils";

const menuItems = [
  { label: "Home", href: "/#top" },
  { label: "About", href: "/#about" },
  { label: "The story", href: "/#story" },
  { label: "Skills", href: "/#skills" },
  { label: "Ask my graph", href: "/graph" },
  { label: "Contact", href: "/#contact" },
];

/** Fixed top bar from the 21st.dev hero: menu on the left, monogram in the middle, CTA on the right. */
export function SiteNav() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const location = useLocation();

  useEffect(() => setOpen(false), [location]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => menuRef.current && !menuRef.current.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-50 transition-colors duration-300",
        scrolled ? "border-b border-white/5 bg-background/80 backdrop-blur-md" : "bg-transparent",
      )}
    >
      <nav className="mx-auto flex h-16 max-w-screen-2xl items-center justify-between px-4 sm:px-6">
        <div ref={menuRef} className="relative">
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? "Close menu" : "Open menu"}
            className="rounded-md p-2 text-neutral-400 transition-colors hover:text-white"
          >
            {open ? <X className="h-7 w-7" strokeWidth={2} /> : <Menu className="h-7 w-7" strokeWidth={2} />}
          </button>
          {open && (
            <div className="absolute left-0 top-full mt-2 w-60 rounded-xl border border-white/10 bg-background/95 p-3 shadow-2xl backdrop-blur-md animate-fade-in">
              {menuItems.map((item) =>
                item.href.startsWith("/#") ? (
                  <a
                    key={item.label}
                    href={item.href}
                    className="block rounded-md px-3 py-2 font-display text-lg font-bold uppercase tracking-tight transition-colors hover:text-brand"
                  >
                    {item.label}
                  </a>
                ) : (
                  <Link
                    key={item.label}
                    to={item.href}
                    className="block rounded-md px-3 py-2 font-display text-lg font-bold uppercase tracking-tight text-brand"
                  >
                    {item.label}
                  </Link>
                ),
              )}
            </div>
          )}
        </div>

        <Link to="/" aria-label="Home" className="font-display text-2xl font-bold tracking-tighter">
          {profile.firstName[0]}
          <span className="text-brand">{profile.lastName[0]}</span>
        </Link>

        <Link
          to="/graph"
          className="group inline-flex items-center gap-2 rounded-full border border-brand/40 px-3 py-1.5 font-mono text-xs text-brand transition-colors hover:bg-brand hover:text-brand-foreground sm:px-4 sm:text-sm"
        >
          <Network className="h-4 w-4" />
          <span className="hidden sm:inline">Ask my career graph</span>
          <span className="sm:hidden">Ask</span>
        </Link>
      </nav>
    </header>
  );
}
