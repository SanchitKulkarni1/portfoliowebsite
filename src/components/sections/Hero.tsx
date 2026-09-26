import { ChevronDown, Github, Linkedin, MapPin } from "lucide-react";
import { BlurText } from "@/components/common/BlurText";
import { profile } from "@/content/profile";

const nameClass =
  "justify-center whitespace-nowrap font-display font-bold uppercase leading-[0.78] tracking-tighter text-brand " +
  "text-[18.5vw] sm:text-[15vw] lg:text-[190px] xl:text-[210px]";

/** Adapted from 21st.dev "Portfolio Hero": giant name with the portrait overlaid in the centre. */
export function Hero() {
  return (
    <section id="top" className="relative flex min-h-[100svh] flex-col overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />

      <div className="relative flex flex-1 items-center justify-center px-2 pt-16">
        <div className="relative text-center">
          <h1 className="sr-only">
            {profile.firstName} {profile.lastName}, {profile.headline}
          </h1>
          <BlurText text={profile.firstName} as="span" animateBy="letters" delay={90} className={nameClass} />
          <br />
          <BlurText text={profile.lastName} as="span" animateBy="letters" delay={90} className={nameClass} />

          <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
            <div className="h-[38vw] w-[23vw] overflow-hidden rounded-full shadow-[0_0_80px_-10px_hsl(var(--brand)/0.45)] ring-1 ring-white/10 transition-transform duration-500 hover:scale-105 sm:h-[30vw] sm:w-[18vw] lg:h-[250px] lg:w-[150px]">
              <img src={profile.photo} alt={`${profile.firstName} ${profile.lastName}`} className="h-full w-full object-cover" />
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 flex flex-col items-center gap-5 px-6 pb-20 text-center sm:pb-24">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-brand sm:text-sm">{profile.headline}</p>
        <BlurText
          text={profile.tagline}
          delay={80}
          className="max-w-2xl justify-center text-lg text-neutral-300 sm:text-xl md:text-2xl"
        />
        <div className="flex flex-wrap items-center justify-center gap-3 text-sm">
          <a
            href="#story"
            className="rounded-full bg-brand px-5 py-2.5 font-semibold text-brand-foreground transition-transform hover:scale-[1.03]"
          >
            Read the story
          </a>
          <a
            href={profile.resumeUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-full border border-white/15 px-5 py-2.5 font-semibold transition-colors hover:border-white/40"
          >
            Résumé
          </a>
          <span className="flex items-center gap-3 pl-1 text-neutral-400">
            <a href={profile.links.github} target="_blank" rel="noreferrer" aria-label="GitHub" className="hover:text-white">
              <Github className="h-5 w-5" />
            </a>
            <a href={profile.links.linkedin} target="_blank" rel="noreferrer" aria-label="LinkedIn" className="hover:text-white">
              <Linkedin className="h-5 w-5" />
            </a>
            <span className="inline-flex items-center gap-1 font-mono text-xs">
              <MapPin className="h-3.5 w-3.5" /> {profile.location}
            </span>
          </span>
        </div>
      </div>

      <a href="#about" aria-label="Scroll down" className="absolute bottom-5 left-1/2 -translate-x-1/2 text-neutral-500 hover:text-white">
        <ChevronDown className="h-6 w-6 animate-bounce" />
      </a>
    </section>
  );
}
