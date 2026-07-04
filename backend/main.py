"""
main.py — Entrypoint da aplicação AI Resume Analyzer.

Inicializa o FastAPI, configura CORS e registra as rotas legadas
(/health, /analyze) e versionadas (/api/v1/health, /api/v1/analyze).

Toda a lógica de validação de upload (SPEC 0008) e de orquestração da
análise vive em app/services e app/engines — este arquivo só faz o
bootstrap da aplicação e o registro das rotas.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.api.v1.routes import analyze, health
from app.core.config import get_cors_allowed_origins

# Inicializa a aplicação FastAPI
app = FastAPI(
    title="AI Resume Analyzer",
    description="Analisa a compatibilidade entre um currículo e uma descrição de vaga.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Configuração de CORS
# Em desenvolvimento: permite qualquer origem (facilita uso com Vite dev server)
# Em produção: restringir ao domínio do frontend via variável FRONTEND_ORIGIN
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rotas legadas (sem prefixo) — preservam /health e /analyze.
# Reaproveitam exatamente as mesmas funções registradas em /api/v1 abaixo,
# sem nenhuma lógica duplicada.
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(analyze.router)

# ---------------------------------------------------------------------------
# Rotas versionadas — /api/v1/health e /api/v1/analyze
# ---------------------------------------------------------------------------
app.include_router(api_v1_router)
