import { GraduationCap } from "lucide-react";
import { SectionHeading } from "@/components/common/SectionHeading";
import { profile } from "@/content/profile";
import { skills } from "@/data/careerGraph";
import { useReveal } from "@/hooks/useReveal";

export function About() {
  const ref = useReveal<HTMLDivElement>();
  const marquee = skills.slice(0, 18).map((s) => s.name);

  return (
    <section id="about" className="relative scroll-mt-16 py-28 sm:py-36">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <SectionHeading index="01" kicker="About" title="I turn messy operational problems into AI systems that ship." />

        <div ref={ref} className="reveal grid gap-12 lg:grid-cols-[1.4fr_1fr]">
          <div className="space-y-6 text-lg leading-relaxed text-neutral-300">
            {profile.about.map((paragraph) => (
              <p key={paragraph.slice(0, 24)}>{paragraph}</p>
            ))}
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {profile.facts.map((fact) => (
                <div key={fact.label} className="rounded-2xl border border-white/10 bg-card p-5">
                  <p className="font-display text-3xl font-bold text-brand">{fact.value}</p>
                  <p className="mt-1 text-sm leading-snug text-muted-foreground">{fact.label}</p>
                </div>
              ))}
            </div>
            <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-card p-5">
              <GraduationCap className="mt-0.5 h-6 w-6 shrink-0 text-brand" />
              <div>
                <p className="font-semibold">{profile.education.degree}</p>
                <p className="text-sm text-muted-foreground">
                  {profile.education.school} · {profile.education.years} · {profile.education.grade}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-24 overflow-hidden border-y border-white/5 py-5 [mask-image:linear-gradient(90deg,transparent,black_12%,black_88%,transparent)]">
        <div className="flex w-max animate-marquee gap-10 font-display text-2xl font-bold uppercase tracking-tight text-neutral-700 sm:text-3xl">
          {[...marquee, ...marquee].map((name, i) => (
            <span key={i} className="flex items-center gap-10">
              {name}
              <span className="text-brand">✦</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
