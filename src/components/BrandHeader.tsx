import { useMemo } from "react";
import { Button } from "@/components/ui/button";

const navItems = [
  { label: "About", href: "#about" },
  { label: "Skills", href: "#skills" },
  { label: "Projects", href: "#projects" },
  { label: "Contact", href: "#contact" },
];

export default function BrandHeader() {
  const items = useMemo(() => navItems, []);
  return (
    <header className="sticky top-0 z-40 border-b bg-background/60 backdrop-blur supports-[backdrop-filter]:bg-background/50">
      <nav className="container flex h-14 items-center justify-between">
        <a href="#home" aria-label="Go to home" className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-brand shadow-glow" />
          <span className="font-display text-lg tracking-wide">Sanchit Kulkarni</span>
        </a>

        <div className="hidden md:flex items-center gap-6">
          {items.map((item) => (
            <a key={item.href} href={item.href} className="story-link text-sm text-muted-foreground hover:text-foreground transition-colors">
              {item.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <Button asChild variant="hero" size="sm">
            <a href="#projects">View Work</a>
          </Button>
        </div>
      </nav>
    </header>
  );
}
