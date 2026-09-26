/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CAREER_GRAPH_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
