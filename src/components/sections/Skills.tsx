import { SectionHeading } from "@/components/common/SectionHeading";
import { skillsByCategory, type SkillCategory } from "@/data/careerGraph";
import { useReveal } from "@/hooks/useReveal";

const TOP_PER_CATEGORY = 8;
const order: SkillCategory[] = ["AI/ML", "Backend", "Data", "Frontend", "Cloud & DevOps", "Tooling"];

export function Skills() {
  const grouped = skillsByCategory();
  const maxUsage = Math.max(...[...grouped.values()].flat().map((s) => s.usage));
  const ref = useReveal<HTMLDivElement>(0.05);

  return (
    <section id="skills" className="scroll-mt-16 py-28 sm:py-36">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <SectionHeading
          index="03"
          kicker="Skills"
          title="Measured by what I've built with them."
          intro="Every skill here is linked to real projects or roles in my career graph. The bar shows how many use it: evidence, not a self-rating."
        />
        <div ref={ref} className="reveal grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {order
            .filter((category) => grouped.has(category))
            .map((category) => (
              <div key={category} className="rounded-2xl border border-white/10 bg-card p-6">
                <h3 className="font-mono text-xs uppercase tracking-[0.25em] text-brand">{category}</h3>
                <ul className="mt-5 space-y-3">
                  {grouped.get(category)!.slice(0, TOP_PER_CATEGORY).map((skill) => (
                    <li key={skill.id}>
                      <div className="flex items-baseline justify-between gap-3 text-sm">
                        <span>{skill.name}</span>
                        <span className="font-mono text-xs text-muted-foreground">×{skill.usage}</span>
                      </div>
                      <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/5">
                        <div className="h-full rounded-full bg-brand/70" style={{ width: `${(skill.usage / maxUsage) * 100}%` }} />
                      </div>
                    </li>
                  ))}
                </ul>
                {grouped.get(category)!.length > TOP_PER_CATEGORY && (
                  <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
                    Also:{" "}
                    {grouped
                      .get(category)!
                      .slice(TOP_PER_CATEGORY)
                      .map((s) => s.name)
                      .join(", ")}
                  </p>
                )}
              </div>
            ))}
        </div>
      </div>
    </section>
  );
}
