import { useReveal } from "@/hooks/useReveal";

interface SectionHeadingProps {
  index: string;
  kicker: string;
  title: string;
  intro?: string;
}

/** Numbered section heading: "02 / THE STORY" kicker, big title, optional intro. */
export function SectionHeading({ index, kicker, title, intro }: SectionHeadingProps) {
  const ref = useReveal<HTMLDivElement>();
  return (
    <div ref={ref} className="reveal mb-14 max-w-3xl">
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-brand">
        {index} / {kicker}
      </p>
      <h2 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl md:text-6xl">
        {title}
      </h2>
      {intro && <p className="mt-6 text-lg leading-relaxed text-muted-foreground">{intro}</p>}
    </div>
  );
}
