import { Badge } from "@/components/ui/badge";

const skills = [
  "Python", "JavaScript", "TypeScript", "React.js", "Node.js", 
  "Express.js", "MongoDB", "PostgreSQL", "Flask", "LLMs", 
  "Langchain", "Tailwind CSS", 
  "REST APIs", "JWT Auth", "Git", "CI/CD","PowerBI"
];

export default function Skills() {
  return (
    <section id="skills" className="container py-16">
      <header className="mb-6">
        <h2 className="font-display text-3xl">Skills</h2>
        <p className="text-muted-foreground">Core technologies and tools I use daily.</p>
      </header>
      <div className="flex flex-wrap gap-2">
        {skills.map((s) => (
          <Badge key={s} variant="secondary" className="px-3 py-1 text-sm">
            {s}
          </Badge>
        ))}
      </div>
    </section>
  );
}
