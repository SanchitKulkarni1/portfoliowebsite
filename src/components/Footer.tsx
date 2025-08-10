export default function Footer() {
  return (
    <footer className="border-t py-8">
      <div className="container flex flex-col items-center justify-between gap-3 md:flex-row">
        <p className="text-sm text-muted-foreground">© {new Date().getFullYear()} Sanchit Kulkarni. All rights reserved.</p>
        <nav className="flex items-center gap-4 text-sm">
          <a href="#about" className="text-muted-foreground hover:text-foreground transition-colors">About</a>
          <a href="#projects" className="text-muted-foreground hover:text-foreground transition-colors">Projects</a>
          <a href="#contact" className="text-muted-foreground hover:text-foreground transition-colors">Contact</a>
        </nav>
      </div>
    </footer>
  );
}
