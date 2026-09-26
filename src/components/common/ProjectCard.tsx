import { ArrowUpRight, Github } from "lucide-react";
import { SkillChip } from "@/components/common/SkillChip";
import type { Project } from "@/data/careerGraph";
import { cn } from "@/lib/utils";

const kindLabel: Record<Project["kind"], string> = { work: "Work", freelance: "Freelance", personal: "Personal" };

interface ProjectCardProps {
  project: Project;
  featured?: boolean;
  maxSkills?: number;
}

export function ProjectCard({ project, featured = false, maxSkills = featured ? 10 : 5 }: ProjectCardProps) {
  const extraSkills = project.skills.length - maxSkills;

  return (
    <article
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-card p-6 transition-colors hover:border-brand/40",
        featured && "sm:p-8",
      )}
    >
      <div className="pointer-events-none absolute -right-24 -top-24 h-48 w-48 rounded-full bg-brand/0 blur-3xl transition-colors duration-500 group-hover:bg-brand/10" />

      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
        <span className="text-brand">{kindLabel[project.kind]}</span>
        <span>·</span>
        <span>{project.year}</span>
        {project.clientName && (
          <>
            <span>·</span>
            <span className="normal-case tracking-normal">for {project.clientName}</span>
          </>
        )}
      </div>

      <h3 className={cn("mt-3 font-display font-bold tracking-tight", featured ? "text-2xl sm:text-3xl" : "text-xl")}>
        {project.name}
      </h3>
      <p className={cn("mt-3 leading-relaxed text-neutral-400", featured ? "text-base sm:text-lg" : "text-sm")}>
        {project.summary}
      </p>

      <div className="mt-5 flex flex-wrap gap-1.5">
        {project.skills.slice(0, maxSkills).map((skill) => (
          <SkillChip key={skill.id} skill={skill} />
        ))}
        {extraSkills > 0 && <span className="px-1 font-mono text-[11px] leading-5 text-muted-foreground">+{extraSkills}</span>}
      </div>

      {(project.demoUrl || project.repoUrl) && (
        <div className="mt-auto flex gap-4 pt-6 text-sm font-medium">
          {project.demoUrl && (
            <a href={project.demoUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-brand hover:underline">
              Live <ArrowUpRight className="h-4 w-4" />
            </a>
          )}
          {project.repoUrl && (
            <a
              href={project.repoUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-neutral-300 hover:text-white"
            >
              <Github className="h-4 w-4" /> Code
            </a>
          )}
        </div>
      )}
    </article>
  );
}
