/**
 * My career as chapters. Each chapter is prose plus references to projects by
 * their career-graph id; the project details (summary, stack, links) come from
 * the graph itself, so they stay in sync with what the chatbot knows.
 */

export interface Chapter {
  id: string;
  period: string;
  title: string;
  story: string;
  /** The one thing this chapter taught me. */
  takeaway: string;
  /** Featured projects first; the first one is shown large. */
  projectIds: string[];
  /** Optional callout for work that deserves special mention. */
  spotlight?: { projectId: string; label: string; note: string };
}

export const chapters: Chapter[] = [
  {
    id: "foundations",
    period: "2022 – 2025",
    title: "Learning by shipping",
    story:
      "At VESIT I learned fastest by building things other people depended on. My first freelance clients were a hospital, a web agency and a construction firm, and the hospital project grew from a website into the software their staff use for appointments, patient records and billing. Alongside that I built ML projects of my own, and helped run college events for 5,000+ people as Deputy Cultural Secretary.",
    takeaway: "Owning a product end to end (requirements, build, deploy, support) teaches more than any course.",
    projectIds: ["anand-hospital-site", "ai-resume-analyzer", "codevertex-site", "idps-ml"],
  },
  {
    id: "balltime",
    period: "Aug 2025 – now",
    title: "Building something of my own",
    story:
      "I co-founded Balltime to give street and local football players a home: profiles, teams, turf booking, leaderboards, chat and full round-robin tournaments with live scoring and MVP voting. I build the product end to end: a React web app and an Expo mobile app on one Supabase backend.",
    takeaway: "Shipping to real users every week keeps you honest about what actually matters.",
    projectIds: ["balltime-platform"],
  },
  {
    id: "ai-in-production",
    period: "Sep 2025 – Feb 2026",
    title: "AI, in production",
    story:
      "As an AI Engineer Intern at The Machine Learning Company I moved from notebooks to systems clients rely on: enterprise RAG chatbots, multi-agent orchestrations and tool-using agents, plus custom YOLOv8 models taken from raw data to optimized inference. On my own time I pushed the same ideas further, into packaging recognition and explainable lead scoring.",
    takeaway: "The model is the easy part. Retrieval, evaluation and latency budgets decide whether it ships.",
    projectIds: ["tmlc-rag-chatbots", "tmlc-yolo-models", "pharma-context-engine", "ai-sales-agent"],
  },
  {
    id: "agents",
    period: "2026",
    title: "Going deep on agents",
    story:
      "I spent early 2026 building agent systems end to end with LangGraph: one that reads a whole GitHub repository and documents its architecture, one that turns plain-English questions into SQL over SAP order-to-cash data, a market-research copilot, and a pricing agent whose LLM auditor can approve, reject or escalate every change.",
    takeaway: "Good agents are mostly good plumbing: typed state, guarded tools and a human escape hatch.",
    projectIds: ["giteq", "dodgeai-fde", "market-research-copilot", "dynamic-pricing-agent"],
  },
  {
    id: "backends",
    period: "Apr – May 2026",
    title: "Backends that hold up",
    story:
      "At Ascent AI (GR2 Engineering) I built production FastAPI services for a client: Entra ID authentication, role-based access, PostgreSQL migrations and gateway-based microservices on AWS. I brought the same discipline to freelance work, with a complete CRM for a football academy and an OCR + LLM pipeline that turns invoices into structured data.",
    takeaway: "Auth, permissions and latency aren't features. They're the product people don't notice until they break.",
    projectIds: ["ascent-secure-backend", "sportzbase-crm", "invoice-extraction"],
  },
  {
    id: "architect",
    period: "Jun 2026 – now",
    title: "Architecting from zero",
    story:
      "At Evenflow Brands I own the core tech for a fast-growing consumer brands company across Ops, Finance, Marketing and Sourcing. That covers system architecture, databases and business logic, and a new production AI system almost every week: price intelligence, debit-note validation, catalog monitoring and the pipelines that feed them.",
    takeaway: "An architect's real job is choosing what not to build.",
    projectIds: ["evenflow-price-intelligence", "evenflow-debit-note-validation", "evenflow-catalog-monitoring", "evenflow-ops-automation"],
    spotlight: {
      projectId: "evenflow-website",
      label: "Frontend spotlight",
      note: "I also rebuilt evenflowbrands.com, adding server-side rendering and a CMS on TanStack Start. I used the same stack for a client's site at prasadenterprisesindia.com.",
    },
  },
];
