# Sanchit Kulkarni · Portfolio

My portfolio, plus a chatbot you can ask about my career. The chatbot answers from a Neo4j knowledge graph of my roles, projects and skills.

```
.
├── frontend/   React + Vite + Tailwind site: the story, projects, skills, and the /graph chat page
├── backend/    FastAPI "Career Graph API": text-to-Cypher GraphRAG over Neo4j with Gemini
└── render.yaml Render blueprint for the backend
```

Both halves read the same dataset, `backend/data/career_graph.json`. Change it once and the site and the chatbot stay in sync.

## Run locally

```bash
# Backend (see backend/README.md for details and tests)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                  # NEO4J_* and GOOGLE_API_KEY
uvicorn app.main:create_app --factory --reload --port 8000

# Frontend
cd frontend
npm install
echo "VITE_CAREER_GRAPH_API_URL=http://localhost:8000" > .env.local
npm run dev                           # http://localhost:8080
```

The site works without the backend. The graph renders from the bundled dataset and the chat shows as offline.

## Deploy

| | Frontend (Vercel) | Backend (Render) |
|---|---|---|
| Root directory | `frontend` | `backend` |
| Build | `npm run build` (output `dist`) | `pip install -r requirements.txt` |
| Start | (static) | `uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'` |
| Env vars | `VITE_CAREER_GRAPH_API_URL` | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `GOOGLE_API_KEY`, `ALLOWED_ORIGINS`, `PYTHON_VERSION=3.11.9` |

On Vercel, keep **"Include files outside the root directory"** enabled: the frontend imports `../backend/data/career_graph.json` at build time.
