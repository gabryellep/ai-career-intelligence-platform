"""
health.py — Rota de health check.

Registrada tanto sem prefixo (rota legada /health) quanto sob /api/v1
(rota versionada /api/v1/health) a partir da mesma função — ver main.py
e app/api/v1/router.py.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check():
    """
    Verifica se o serviço está em execução.
    Retorna {"status": "ok"} com HTTP 200.
    """
    return {"status": "ok"}
