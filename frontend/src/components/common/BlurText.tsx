import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { cn } from "@/lib/utils";

/** Text that blurs in letter-by-letter or word-by-word when it enters the viewport. Adapted from 21st.dev "Portfolio Hero". */
interface BlurTextProps {
  text: string;
  delay?: number;
  animateBy?: "words" | "letters";
  direction?: "top" | "bottom";
  className?: string;
  style?: CSSProperties;
  as?: "p" | "span" | "h1" | "h2";
}

export function BlurText({ text, delay = 50, animateBy = "words", direction = "top", className, style, as = "p" }: BlurTextProps) {
  const [inView, setInView] = useState(false);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => entry.isIntersecting && setInView(true), { threshold: 0.1 });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const segments = useMemo(() => (animateBy === "words" ? text.split(" ") : text.split("")), [text, animateBy]);
  const Tag = as;

  return (
    <Tag ref={ref as never} className={cn("inline-flex flex-wrap", className)} style={style} aria-label={text}>
      {segments.map((segment, i) => (
        <span
          key={i}
          aria-hidden
          style={{
            display: "inline-block",
            filter: inView ? "blur(0px)" : "blur(10px)",
            opacity: inView ? 1 : 0,
            transform: inView ? "translateY(0)" : `translateY(${direction === "top" ? "-20px" : "20px"})`,
            transition: `all 0.5s ease-out ${i * delay}ms`,
          }}
        >
          {segment}
          {animateBy === "words" && i < segments.length - 1 ? " " : ""}
        </span>
      ))}
    </Tag>
  );
}
