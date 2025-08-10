import BrandHeader from "@/components/BrandHeader";
import Hero from "@/components/sections/Hero";
import Skills from "@/components/sections/Skills";
import Projects from "@/components/sections/Projects";
import Contact from "@/components/sections/Contact";
import Footer from "@/components/Footer";
import SanchitPic2 from "./../../images/SanchitPic2.jpeg"


const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <BrandHeader />
      <main>
        <Hero />
        <section id="about" className="container py-16">
          <h2 className="font-display text-3xl mb-8">About</h2>
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div className="flex justify-center md:justify-start">
              <div className="w-48 h-48 md:w-64 md:h-64 rounded-full ring-4 ring-brand/20 overflow-hidden shadow-lg">
                <img 
                  src={SanchitPic2} 
                  alt="Sanchit Kulkarni" 
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const fallback = target.nextElementSibling as HTMLElement;
                    if (fallback) fallback.style.display = 'flex';
                  }}
                />
                <div className="w-full h-full bg-gradient-to-br from-brand/20 to-brand/40 flex items-center justify-center text-4xl font-bold text-brand">
                  SK
                </div>
              </div>
            </div>
            <div>
              <p className="text-muted-foreground leading-relaxed">I’m Sanchit Kulkarni, an Electronics & Computer Science undergraduate passionate about building scalable, intelligent, and user-focused applications. I specialize in full-stack development and AI/ML engineering, with experience delivering real-world projects — from AI-powered resume analyzers and research collaboration platforms to route optimization systems and hospital management apps.

I’ve worked with clients, startups, and internships, leading projects end-to-end — from requirements to deployment — while ensuring clean code, strong architecture, and performance at scale.

Beyond development, I’ve served as Deputy Cultural Secretary at VESIT, managing large-scale events for 5,000+ participants, honing my leadership, collaboration, and problem-solving skills.</p>
            </div>
          </div>
        </section>
        <Skills />
        <Projects />
        <Contact />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
