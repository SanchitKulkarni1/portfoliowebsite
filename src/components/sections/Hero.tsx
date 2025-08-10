import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import ContactModal from "@/components/ContactModal";
import { Github, Linkedin, Mail } from "lucide-react";
import { useEffect, useRef } from "react";

import SanchitPic1 from "./../../../images/SanchitPic1.jpeg"

export default function Hero() {
  const glowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = glowRef.current;
    if (!el) return;
    const onMove = (e: MouseEvent) => {
      const rect = document.body.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      el.style.setProperty("--x", `${x}%`);
      el.style.setProperty("--y", `${y}%`);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <section id="home" className="relative overflow-hidden">
      <div ref={glowRef} aria-hidden className="glow-field" />

      <div className="container flex min-h-[78vh] flex-col items-center justify-center py-20 text-center">
        <div className="mb-6">
          <div className="mx-auto w-28 h-28 md:w-32 md:h-32 rounded-full ring-1 ring-primary/20 overflow-hidden">
            <Avatar className="w-28 h-28 md:w-32 md:h-32">
              <AvatarImage src={SanchitPic1} alt="Sanchit Kulkarni" loading="lazy" />
              <AvatarFallback>YN</AvatarFallback>
            </Avatar>
          </div>
        </div>
        <p className="mb-4 text-lg font-medium text-brand animate-fade-in">AI/ML Engineer & FullStack Developer</p>
        <h1 className="font-display text-5xl md:text-6xl font-semibold tracking-tight animate-enter">
        Crafting smart, scalable products powered by AI and modern web tech.
        </h1>
        <p className="mt-5 max-w-2xl text-lg text-foreground animate-fade-in">
        I build intelligent, high-performance apps that don’t just work — they solve real problems.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3 animate-scale-in">
          <Button variant="hero" size="lg" asChild>
            <a href="https://drive.google.com/file/d/1LJw6cYZF8DpFagaSVzA6VIHuOVyVzdbZ/view?usp=sharing">My Resume</a>
          </Button>
          <Button variant="hero" size="lg" asChild>
            <a href="#contact">Contact Me</a>
          </Button>
        </div>

        <div className="mt-8 flex items-center gap-4 text-muted-foreground">
          <a className="hover-scale" href="https://github.com/SanchitKulkarni1" aria-label="GitHub"><Github /></a>
          <a className="hover-scale" href="https://www.linkedin.com/in/sanchit-kulkarni-22007529b/" aria-label="LinkedIn"><Linkedin /></a>
          <ContactModal  trigger={<button className="hover-scale" aria-label="Email"><Mail /></button>} />
        </div>
      </div>
    </section>
  );
}
