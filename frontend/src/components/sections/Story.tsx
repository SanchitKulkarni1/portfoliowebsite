import { Sparkles } from "lucide-react";
import { ProjectCard } from "@/components/common/ProjectCard";
import { SectionHeading } from "@/components/common/SectionHeading";
import { chapters, type Chapter } from "@/content/story";
import { projectById } from "@/data/careerGraph";
import { useReveal } from "@/hooks/useReveal";

function ChapterBlock({ chapter, index }: { chapter: Chapter; index: number }) {
  const ref = useReveal<HTMLDivElement>(0.08);
  const [lead, ...rest] = chapter.projectIds.map(projectById);
  const spotlight = chapter.spotlight && projectById(chapter.spotlight.projectId);

  return (
    <div ref={ref} className="reveal grid gap-10 border-t border-white/10 py-16 lg:grid-cols-[minmax(0,360px)_1fr] lg:gap-16">
      <div className="lg:sticky lg:top-24 lg:self-start">
        <p className="font-mono text-sm text-brand">
          {String(index + 1).padStart(2, "0")} <span className="text-muted-foreground">/ {chapter.period}</span>
        </p>
        <h3 className="mt-3 font-display text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{chapter.title}</h3>
        <p className="mt-5 leading-relaxed text-neutral-300">{chapter.story}</p>
        <p className="mt-6 border-l-2 border-brand pl-4 text-sm italic leading-relaxed text-neutral-400">{chapter.takeaway}</p>
      </div>

      <div className="space-y-4">
        <ProjectCard project={lead} featured />
        {rest.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2">
            {rest.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}
        {chapter.spotlight && spotlight && (
          <div className="rounded-2xl border border-brand/30 bg-brand/[0.04] p-6">
            <p className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-brand">
              <Sparkles className="h-4 w-4" /> {chapter.spotlight.label}
            </p>
            <p className="mt-3 text-neutral-300">{chapter.spotlight.note}</p>
            <div className="mt-5">
              <ProjectCard project={spotlight} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function Story() {
  return (
    <section id="story" className="scroll-mt-16 py-28 sm:py-36">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <SectionHeading
          index="02"
          kicker="The story"
          title="Six chapters, one habit: ship it."
          intro="How I went from college projects to architecting production AI. Each chapter shows the work it produced and the stack behind it."
        />
        {chapters.map((chapter, index) => (
          <ChapterBlock key={chapter.id} chapter={chapter} index={index} />
        ))}
      </div>
    </section>
  );
}
