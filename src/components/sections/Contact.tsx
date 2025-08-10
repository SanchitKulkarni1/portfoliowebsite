import { Button } from "@/components/ui/button";
import ContactModal from "@/components/ContactModal";

export default function Contact() {
  return (
    <section id="contact" className="container py-20">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="font-display text-3xl md:text-4xl">Let’s build something great</h2>
        <p className="mt-3 text-muted-foreground">I’m open to full‑time roles and impactful freelance projects.</p>
        <div className="mt-6 flex items-center justify-center gap-3">
          <ContactModal
            targetEmail="you@example.com"
            trigger={<Button variant="hero">Email Me</Button>}
          />
          <Button asChild variant="soft">
            <a href="#projects">See Projects</a>
          </Button>
        </div>
      </div>
    </section>
  );
}
