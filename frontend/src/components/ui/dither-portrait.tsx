/**
 * Portrait rendered as a brand-coloured ordered dither on a canvas; hovering (or tapping)
 * wipes it away to reveal the real photo, and the card tilts toward the pointer.
 *
 * Dithering adapted from 21st.dev "Dither Image" (educalvolpz): Bayer ordered dither over a
 * luminance grid, mapped onto a colour ramp. Changes: sizes itself to its container, fixed
 * brand palette with a contrast curve, CSS-only reveal (no motion dependency), tilt + glare.
 */
import { useEffect, useRef, useState, type PointerEvent } from "react";
import { cn } from "@/lib/utils";

type Rgb = [number, number, number];

interface DitherPortraitProps {
  src: string;
  alt: string;
  /** Colour ramp from dark to light, as CSS colours. */
  palette?: string[];
  /** Size of one dither block in CSS pixels. */
  pixelSize?: number;
  /** Where the subject's face is, as fractions of width and height. The vignette centres here. */
  focus?: [number, number];
  /** Width / height. */
  aspectRatio?: number;
  className?: string;
}

const BAYER_SIZE = 8;
const BAYER = [
  0, 32, 8, 40, 2, 34, 10, 42, 48, 16, 56, 24, 50, 18, 58, 26, 12, 44, 4, 36, 14, 46, 6, 38, 60, 28, 52, 20, 62, 30, 54,
  22, 3, 35, 11, 43, 1, 33, 9, 41, 51, 19, 59, 27, 49, 17, 57, 25, 15, 47, 7, 39, 13, 45, 5, 37, 63, 31, 55, 23, 61, 29,
  53, 21,
];
const MAX_DPR = 2;
const MAX_TILT_DEG = 7;

function parseColor(scratch: CanvasRenderingContext2D, value: string): Rgb {
  scratch.clearRect(0, 0, 1, 1);
  scratch.fillStyle = value;
  scratch.fillRect(0, 0, 1, 1);
  const { data } = scratch.getImageData(0, 0, 1, 1);
  return [data[0], data[1], data[2]];
}

/** Draw `image` into a w×h box like CSS object-fit: cover. */
function drawCover(ctx: CanvasRenderingContext2D, image: HTMLImageElement, w: number, h: number) {
  const scale = Math.max(w / image.naturalWidth, h / image.naturalHeight);
  const dw = image.naturalWidth * scale;
  const dh = image.naturalHeight * scale;
  ctx.drawImage(image, (w - dw) / 2, (h - dh) / 2, dw, dh);
}

export function DitherPortrait({
  src,
  alt,
  palette = ["hsl(0, 0%, 3%)", "hsl(71, 60%, 14%)", "hsl(71, 65%, 30%)", "hsl(71, 78%, 52%)"],
  pixelSize = 3,
  focus = [0.5, 0.36],
  aspectRatio = 4 / 5,
  className,
}: DitherPortraitProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(0);
  const [ready, setReady] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0, gx: 50, gy: 50 });

  // Track the rendered width so the dither grid matches the element exactly.
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.round(entry.contentRect.width)));
    observer.observe(frame);
    return () => observer.disconnect();
  }, []);

  const paletteKey = palette.join("|");
  const [focusX, focusY] = focus;
  // Finer blocks on small renders so the face stays readable.
  const blockSize = width > 0 && width < 360 ? Math.max(1, pixelSize - 1) : pixelSize;
  const [canHover, setCanHover] = useState(true);
  useEffect(() => setCanHover(window.matchMedia("(hover: hover)").matches), []);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || width === 0) return;
    const height = Math.round(width / aspectRatio);
    const ctx = canvas.getContext("2d");
    const scratch = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
    const grid = document.createElement("canvas");
    const gctx = grid.getContext("2d", { willReadFrequently: true });
    if (!ctx || !scratch || !gctx) return;

    let cancelled = false;
    const image = new Image();
    image.decoding = "async";
    image.onload = () => {
      if (cancelled) return;
      const gw = Math.max(1, Math.round(width / blockSize));
      const gh = Math.max(1, Math.round(height / blockSize));
      grid.width = gw;
      grid.height = gh;
      drawCover(gctx, image, gw, gh);
      const frame = gctx.getImageData(0, 0, gw, gh);
      const { data } = frame;
      const ramp = paletteKey.split("|").map((c) => parseColor(scratch, c));
      const steps = ramp.length - 1;

      // Luminance, then auto-levels between the 3rd and 97th percentile.
      const lum = new Float32Array(gw * gh);
      for (let i = 0; i < lum.length; i++) {
        const o = i * 4;
        lum[i] = (data[o] * 0.2126 + data[o + 1] * 0.7152 + data[o + 2] * 0.0722) / 255;
      }
      const sorted = Float32Array.from(lum).sort();
      const lo = sorted[Math.floor(sorted.length * 0.03)];
      const hi = sorted[Math.floor(sorted.length * 0.97)];
      const span = Math.max(0.05, hi - lo);

      for (let i = 0; i < lum.length; i++) {
        const x = i % gw;
        const y = (i / gw) | 0;
        let v = Math.min(1, Math.max(0, (lum[i] - lo) / span));
        v = Math.pow(v, 0.85);
        // Vignette centred on the face: the background falls away, the subject stays lit.
        const dx = (x / gw - focusX) / 0.62;
        const dy = (y / gh - focusY) / 0.8;
        v *= 1 - Math.min(0.85, Math.max(0, Math.hypot(dx, dy) - 0.28) * 1.6);
        v += ((BAYER[(y % BAYER_SIZE) * BAYER_SIZE + (x % BAYER_SIZE)] + 0.5) / 64 - 0.5) / steps;
        const tone = ramp[Math.min(steps, Math.max(0, Math.round(v * steps)))];
        const o = i * 4;
        data[o] = tone[0];
        data[o + 1] = tone[1];
        data[o + 2] = tone[2];
      }
      gctx.putImageData(frame, 0, 0);

      const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(grid, 0, 0, canvas.width, canvas.height);
      setReady(true);
    };
    image.src = src;
    return () => {
      cancelled = true;
      image.onload = null;
    };
  }, [width, aspectRatio, blockSize, paletteKey, src, focusX, focusY]);

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (e.pointerType !== "mouse") return;
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    setTilt({ x: (0.5 - py) * 2 * MAX_TILT_DEG, y: (px - 0.5) * 2 * MAX_TILT_DEG, gx: px * 100, gy: py * 100 });
  };

  const reset = () => {
    setRevealed(false);
    setTilt({ x: 0, y: 0, gx: 50, gy: 50 });
  };

  return (
    <div className={cn("[perspective:1000px]", className)}>
      <div
        ref={frameRef}
        role="img"
        aria-label={alt}
        tabIndex={0}
        onPointerEnter={(e) => e.pointerType === "mouse" && setRevealed(true)}
        onPointerMove={onPointerMove}
        onPointerLeave={reset}
        onClick={() => setRevealed((r) => !r)}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && setRevealed((r) => !r)}
        onBlur={reset}
        className="group relative w-full cursor-crosshair overflow-hidden rounded-2xl border border-brand/25 bg-background shadow-[0_0_90px_-20px_hsl(var(--brand)/0.45)] outline-none transition-transform duration-300 ease-out will-change-transform focus-visible:ring-2 focus-visible:ring-brand"
        style={{
          aspectRatio,
          transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
        }}
      >
        <img src={src} alt="" aria-hidden className="absolute inset-0 h-full w-full object-cover" />

        {/* Dither layer: wipes upward to reveal the photo. */}
        <canvas
          ref={canvasRef}
          aria-hidden
          className={cn(
            "absolute inset-0 h-full w-full transition-[clip-path,opacity] duration-700 ease-[cubic-bezier(0.23,1,0.32,1)]",
            ready ? "opacity-100" : "opacity-0",
          )}
          style={{
            imageRendering: "pixelated",
            clipPath: revealed ? "inset(0% 0% 100% 0%)" : "inset(0% 0% 0% 0%)",
          }}
        />

        {/* Scan line riding the edge of the wipe. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 h-px bg-brand shadow-[0_0_14px_2px_hsl(var(--brand)/0.8)] transition-[top,opacity] duration-700 ease-[cubic-bezier(0.23,1,0.32,1)]"
          style={{ top: revealed ? "0%" : "100%", opacity: revealed ? 0 : 1 }}
        />

        {/* Pointer glare. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
          style={{
            background: `radial-gradient(circle at ${tilt.gx}% ${tilt.gy}%, hsl(0 0% 100% / 0.14), transparent 55%)`,
          }}
        />

        <span className="pointer-events-none absolute bottom-3 left-3 rounded-full border border-white/10 bg-black/60 px-2.5 py-1 font-mono text-[10px] uppercase tracking-widest text-brand backdrop-blur transition-opacity duration-300 group-hover:opacity-0">
          {canHover ? "hover to reveal" : revealed ? "tap to dither" : "tap to reveal"}
        </span>
      </div>
    </div>
  );
}
