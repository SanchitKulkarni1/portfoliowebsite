import { Card, CardContent, CardHeader, CardTitle, CardDescription,} from "@/components/ui/card";
import ResumeAnalyzer from "./../../../images/ResumeAnalyzer.png";
import AnandHospital from "./../../../images/AnandHospital.png";
import Codevertex from "./../../../images/Codevertex.png";
import CollabSphere from "./../../../images/Collabsphere.png";
import MovieChatbot from "./../../../images/MovieChatbot.png";
import HeartPrediction from "./../../../images/HeartPrediction.png";
import { Github, ExternalLink, Globe } from "lucide-react";

const projects = [
  {
    title: "AI Powered Resume Analyzer",
    thumbnail: ResumeAnalyzer,
    projectType: "Personal",
    description: "Analyzes resumes against job descriptions, giving a match score, detailed feedback, and a career roadmap.",
    tags: ["React", "FastAPI", "Langchain", "ChromaDB"],
    repo: "https://github.com/SanchitKulkarni1/AI-Resume-Analyzer.backend",
    demo: "https://ai-resume-analyzer-frontend-wheat.vercel.app/"
  },
  {
    title: "Anand Hospital -Web Platform",
    thumbnail: AnandHospital,
    projectType: "Freelancing",
    description: "Built and deployed, a responsive hospital website with streamlined appointment booking, patient information management, and an intuitive, mobile-friendly UI.",
    tags: ["React", "Typescript", "MongoDB"],
    repo: "https://github.com/SanchitKulkarni1/CollabSphere.git",
    demo: "https://anandhospitalboisar.in/"
  },
  {
    title: "Codevertex -Web Platform",
    thumbnail: Codevertex,
    projectType: "Freelancing",
    description: "Built and deployed, a responsive website for a web services firm with a sleek, modern design and interactive features.",
    tags: ["React", "Typescript", "Three.js", "MongoDB"],
    repo: "https://github.com/SanchitKulkarni1/Codevertex.git",
    demo: "https://www.codevertex.in/"
  },
  {
    title: "Movie Recommendation Chatbot",
    thumbnail: MovieChatbot,
    projectType: "Personal",
    description: "Chatbot that suggests movies by analyzing user input with TF-IDF vectorization and cosine similarity for personalized recommendations.",
    tags: ["Python", "TF-IDF", "Flask"],
    repo: "https://github.com/SanchitKulkarni1/MovieRecommendationChatBot.git",
    //demo: "https://www.codevertex.in/"
  },
  {
    title: "Heart Disease Prediction with AI",
    thumbnail: HeartPrediction,
    projectType: "Personal",
    description: "Real-time heart health monitoring web app that uses an ML model to predict heart attack risk from live patient data with 90% accuracy",
    tags: ["React","Supabase","Python", "Random Forest", "Flask"],
    //repo: "https://github.com/SanchitKulkarni1/MovieRecommendationChatBot.git",
    //demo: "https://www.codevertex.in/"
  },
  {
    title: "CollabSphere -Research Collaboration Platform",
    thumbnail: CollabSphere,
    projectType: "Hackathon",
    description: "A platform for researchers to search papers, collaborate in groups, and get AI-based summaries.",
    tags: ["GeminiAPI", "Flask", "Python"],
    repo: "https://github.com/SanchitKulkarni1/CollabSphere.git",
    //demo: "https://www.codevertex.in/",
  }
];

export default function Projects() {
  return (
    <section id="projects" className="container py-20">
      <header className="mb-10">
        <h2 className="font-display text-3xl md:text-4xl">Selected Projects</h2>
        <p className="text-muted-foreground">A few things I recently worked on</p>
      </header>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {projects.map((p) => (
          <Card key={p.title} className="group relative overflow-hidden border-muted/40 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/40 transition-transform duration-200 hover:-translate-y-1">
            <CardHeader>
              <img src={p.thumbnail} alt={p.title} width={150} height={600} className="w-full h-49 object-cover rounded-md mb-3" />
              <CardTitle className="font-display text-xl">{p.title}</CardTitle>
                             <div className="inline-block px-2 py-1 text-xs font-medium bg-brand/10 text-brand border border-brand/20 rounded-full mb-2">
                 {p.projectType}
               </div>
              <CardDescription>{p.description}</CardDescription>
            </CardHeader>
            <CardContent className="pt-2">
              <ul className="mb-4 flex flex-wrap gap-2 text-xs text-muted-foreground">
                {p.tags.map(t => (
                  <li key={t} className="rounded-md border border-border/60 px-2 py-1">{t}</li>
                ))}
              </ul>
              <div className="flex items-center gap-3 text-sm">
                <a href={p.repo} className="story-link inline-flex items-center gap-1" aria-label={`${p.title} repository`}>
                  <Github className="h-4 w-4" /> 
                </a>
                <a href={p.demo} className="story-link inline-flex items-center gap-1" aria-label={`${p.title} live demo`}>
                  <ExternalLink className="h-4 w-4" /> 
                </a>
              </div>
            </CardContent>
            <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100" style={{ boxShadow: "var(--shadow-glow)" }} />
          </Card>
        ))}
      </div>
    </section>
  );
}
