import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface PortraitProps {
  src: string;
  alt: string;
  className?: string;
  /** Delay before the fade-in starts, in ms. */
  delay?: number;
}

/** Clean portrait card that fades in with the same blur-and-drop motion as BlurText. */
export function Portrait({ src, alt, className, delay = 250 }: PortraitProps) {
  const ref = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [inView, setInView] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => entry.isIntersecting && setInView(true), { threshold: 0.1 });
    observer.observe(el);
    // A cached image can finish loading before React attaches onLoad.
    if (imgRef.current?.complete) setLoaded(true);
    return () => observer.disconnect();
  }, []);

  const visible = inView && loaded;

  return (
    <div
      ref={ref}
      className={cn(
        "overflow-hidden rounded-2xl border border-white/10 bg-card shadow-[0_0_80px_-30px_hsl(var(--brand)/0.35)]",
        className,
      )}
      style={{
        aspectRatio: "4 / 5",
        filter: visible ? "blur(0px)" : "blur(10px)",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(-20px)",
        transition: `filter 0.8s ease-out ${delay}ms, opacity 0.8s ease-out ${delay}ms, transform 0.8s ease-out ${delay}ms`,
      }}
    >
      <img
        src={src}
        alt={alt}
        ref={imgRef}
        onLoad={() => setLoaded(true)}
        className="h-full w-full object-cover"
      />
    </div>
  );
}
