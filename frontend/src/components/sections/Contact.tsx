import { ArrowUpRight, FileText, Github, Linkedin, Mail } from "lucide-react";
import ContactModal from "@/components/ContactModal";
import { profile } from "@/content/profile";
import { useReveal } from "@/hooks/useReveal";

export function Contact() {
  const ref = useReveal<HTMLDivElement>();
  const links = [
    { label: "GitHub", href: profile.links.github, icon: Github },
    { label: "LinkedIn", href: profile.links.linkedin, icon: Linkedin },
    ...(profile.resumeUrl ? [{ label: "Résumé", href: profile.resumeUrl, icon: FileText }] : []),
  ];

  return (
    <section id="contact" className="scroll-mt-16 border-t border-white/5 py-28 sm:py-36">
      <div ref={ref} className="reveal mx-auto max-w-6xl px-5 text-center sm:px-8">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-brand">04 / Contact</p>
        <h2 className="mx-auto mt-6 max-w-4xl font-display text-5xl font-bold leading-[0.95] tracking-tighter sm:text-7xl">
          Have a problem worth automating?
        </h2>
        <p className="mx-auto mt-6 max-w-xl text-lg text-neutral-400">
          I'm open to AI engineering and architecture roles, and to freelance builds that need to actually ship.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <ContactModal
            trigger={
              <button className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 font-semibold text-brand-foreground transition-transform hover:scale-[1.03]">
                <Mail className="h-4 w-4" /> Send me a message
              </button>
            }
          />
          <a
            href={`mailto:${profile.email}`}
            className="rounded-full border border-white/15 px-6 py-3 font-mono text-sm transition-colors hover:border-white/40"
          >
            {profile.email}
          </a>
        </div>

        <div className="mt-10 flex flex-wrap justify-center gap-6 text-sm text-neutral-400">
          {links.map(({ label, href, icon: Icon }) => (
            <a key={label} href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 hover:text-white">
              <Icon className="h-4 w-4" /> {label} <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
