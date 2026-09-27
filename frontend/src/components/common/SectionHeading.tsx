import { useReveal } from "@/hooks/useReveal";
import { cn } from "@/lib/utils";

interface SectionHeadingProps {
  index: string;
  kicker: string;
  title: string;
  intro?: string;
}

/**
 * Numbered section heading: "02 / THE STORY" kicker, big title, optional intro.
 * On wide screens the intro sits beside the title (bottom-aligned) instead of under it,
 * so the heading uses the full width rather than leaving an empty block on the right.
 */
export function SectionHeading({ index, kicker, title, intro }: SectionHeadingProps) {
  const ref = useReveal<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={cn("reveal mb-14", intro && "lg:grid lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)] lg:items-end lg:gap-16")}
    >
      <div className={cn(!intro && "max-w-5xl")}>
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-brand">
          {index} / {kicker}
        </p>
        <h2 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-balance sm:text-5xl md:text-6xl">
          {title}
        </h2>
      </div>
      {intro && <p className="mt-6 text-lg leading-relaxed text-muted-foreground lg:mt-0">{intro}</p>}
    </div>
  );
}
