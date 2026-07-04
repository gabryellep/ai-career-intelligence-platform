"""
router.py — Agregador de rotas da API v1.

health e analyze são reaproveitados também sem prefixo em main.py (rotas
legadas /health e /analyze), evitando duplicação de lógica entre as rotas
legadas e as versionadas. analyses (SPEC 0005) e analytics (SPEC 0006)
existem apenas sob /api/v1 — não há rota legada equivalente, por decisão
explícita de cada uma dessas Specs.
"""

from fastapi import APIRouter

from app.api.v1.routes import analyses, analytics, analyze, health

router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(analyze.router)
router.include_router(analyses.router)
router.include_router(analytics.router)
