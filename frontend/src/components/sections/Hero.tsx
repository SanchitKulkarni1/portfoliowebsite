import { ChevronDown, Github, Linkedin, MapPin } from "lucide-react";
import { BlurText } from "@/components/common/BlurText";
import { Portrait } from "@/components/common/Portrait";
import { profile } from "@/content/profile";

// Line height must come after the size classes: tailwind-merge drops a leading-* that precedes a text-* size.
const nameClass =
  "whitespace-nowrap font-display font-bold uppercase tracking-tighter text-brand " +
  "justify-center text-[17vw] sm:text-[14vw] lg:justify-start lg:text-[118px] xl:text-[150px] leading-[0.9]";

/** Giant name on the left, portrait on the right (stacked on small screens). */
export function Hero() {
  const portrait = (
    <Portrait
      src={profile.photo}
      alt={`${profile.firstName} ${profile.lastName}`}
      className="w-[min(72vw,300px)] sm:w-[320px] lg:w-full lg:max-w-[400px]"
    />
  );

  return (
    <section id="top" className="relative flex min-h-[100svh] flex-col overflow-hidden bg-background">
      <div className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />

      <div className="page-container relative flex flex-1 items-center pb-16 pt-24 lg:pb-12">
        <div className="grid w-full items-center gap-10 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,0.85fr)] lg:gap-12">
          <div className="flex flex-col items-center gap-8 text-center lg:items-start lg:text-left">
            <h1 className="sr-only">
              {profile.firstName} {profile.lastName}, {profile.headline}
            </h1>
            <div aria-hidden className="flex flex-col items-center lg:items-start">
              <BlurText text={profile.firstName} as="span" animateBy="letters" delay={90} className={nameClass} />
              <BlurText text={profile.lastName} as="span" animateBy="letters" delay={90} className={nameClass} />
            </div>

            <div className="lg:hidden">{portrait}</div>

            <div className="flex flex-col items-center gap-5 lg:items-start">
              <p className="font-mono text-xs uppercase tracking-[0.35em] text-brand sm:text-sm">{profile.headline}</p>
              <BlurText
                text={profile.tagline}
                delay={80}
                className="max-w-xl justify-center text-lg text-neutral-300 sm:text-xl md:text-2xl lg:justify-start"
              />
              <div className="flex flex-wrap items-center justify-center gap-3 text-sm lg:justify-start">
                <a
                  href="#story"
                  className="rounded-full bg-brand px-5 py-2.5 font-semibold text-brand-foreground transition-transform hover:scale-[1.03]"
                >
                  Read the story
                </a>
                {profile.resumeUrl && (
                  <a
                    href={profile.resumeUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-full border border-white/15 px-5 py-2.5 font-semibold transition-colors hover:border-white/40"
                  >
                    Résumé
                  </a>
                )}
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
          </div>

          <div className="hidden justify-end lg:flex">{portrait}</div>
        </div>
      </div>

      <a href="#about" aria-label="Scroll down" className="absolute bottom-5 left-1/2 -translate-x-1/2 text-neutral-500 hover:text-white">
        <ChevronDown className="h-6 w-6 animate-bounce" />
      </a>
    </section>
  );
}
