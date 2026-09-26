import type { Skill, SkillCategory } from "@/data/careerGraph";
import { cn } from "@/lib/utils";

const categoryStyle: Record<SkillCategory, string> = {
  "AI/ML": "border-brand/40 text-brand",
  Backend: "border-sky-400/30 text-sky-300",
  Data: "border-violet-400/30 text-violet-300",
  "Cloud & DevOps": "border-amber-400/30 text-amber-300",
  Frontend: "border-pink-400/30 text-pink-300",
  Tooling: "border-zinc-500/40 text-zinc-300",
};

export function SkillChip({ skill, className }: { skill: Pick<Skill, "name" | "category">; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border bg-white/[0.02] px-2.5 py-0.5 font-mono text-[11px] leading-5",
        categoryStyle[skill.category] ?? categoryStyle.Tooling,
        className,
      )}
    >
      {skill.name}
    </span>
  );
}
