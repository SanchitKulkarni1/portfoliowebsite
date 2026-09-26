import { SiteNav } from "@/components/layout/SiteNav";
import { About } from "@/components/sections/About";
import { AskTeaser } from "@/components/sections/AskTeaser";
import { Contact } from "@/components/sections/Contact";
import { Hero } from "@/components/sections/Hero";
import { Skills } from "@/components/sections/Skills";
import { Story } from "@/components/sections/Story";
import Footer from "@/components/Footer";

const Index = () => (
  <div className="min-h-screen bg-background">
    <SiteNav />
    <main>
      <Hero />
      <About />
      <Story />
      <AskTeaser />
      <Skills />
      <Contact />
    </main>
    <Footer />
  </div>
);

export default Index;
