/** Who I am and how to reach me. Narrative copy lives here; facts about projects come from the graph. */

export const profile = {
  firstName: "Sanchit",
  lastName: "Kulkarni",
  headline: "AI Solutions Architect",
  tagline: "I design and ship production AI systems, and the backends they run on.",
  location: "Bengaluru, India",
  email: "sanchit.kulkarni2004@gmail.com",
  resumeUrl: "/Sanchit_Kulkarni_Resume.pdf",
  photo: "/images/sanchit-portrait.webp",
  links: {
    github: "https://github.com/SanchitKulkarni1",
    linkedin: "https://www.linkedin.com/in/sanchit-kulkarni-developer",
  },
  about: [
    "I'm an AI Solutions Architect at Evenflow Brands in Bengaluru, where I build the company's core systems from scratch. Most weeks start with a messy operational problem and end with a production AI system that makes it go away.",
    "I like the whole stack of a problem: scoping it with the people who have it, designing the data model, wiring up agents and retrieval, and shipping a UI people actually use. I also co-founded Balltime, a football community platform, and I still take on freelance builds.",
  ],
  facts: [
    { value: "3", label: "roles in industry since 2025" },
    { value: "1", label: "startup co-founded" },
    { value: "6", label: "freelance clients shipped" },
    { value: "5,000+", label: "people at college events I helped run" },
  ],
  education: {
    school: "VESIT, Mumbai",
    degree: "B.Tech, Electronics & Computer Science",
    years: "2022 – 2026",
    grade: "CGPA 8.51 / 10",
  },
} as const;
