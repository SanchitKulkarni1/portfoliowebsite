/**
 * Renders the small Markdown subset the answer model produces (paragraphs, "*"/"-" bullet
 * lists, **bold**, bare URLs) as React elements. No HTML is ever injected.
 */
import { Fragment, type ReactNode } from "react";

const INLINE = /(\*\*[^*]+\*\*|https?:\/\/[^\s)]+|`[^`]+`)/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i} className="font-semibold text-white">{part.slice(2, -2)}</strong>;
    if (/^https?:\/\//.test(part))
      return (
        <a key={i} href={part.replace(/[.,]$/, "")} target="_blank" rel="noreferrer" className="text-brand underline-offset-2 hover:underline">
          {part}
        </a>
      );
    if (part.startsWith("`") && part.endsWith("`")) return <code key={i} className="rounded bg-white/10 px-1 font-mono text-[0.85em]">{part.slice(1, -1)}</code>;
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function RichText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) {
      blocks.push(
        <ul key={`ul-${blocks.length}`} className="my-2 space-y-1.5">
          {bullets.map((b, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-[0.55em] h-1 w-1 shrink-0 rounded-full bg-brand" />
              <span>{inline(b)}</span>
            </li>
          ))}
        </ul>,
      );
      bullets = [];
    }
  };

  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[*-]\s+(.*)$/);
    if (bullet) {
      bullets.push(bullet[1]);
    } else {
      flush();
      if (line) blocks.push(<p key={`p-${blocks.length}`} className="my-2 first:mt-0">{inline(line)}</p>);
    }
  }
  flush();
  return <div className="leading-relaxed">{blocks}</div>;
}
