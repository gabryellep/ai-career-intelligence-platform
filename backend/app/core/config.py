"""
config.py — Configuração centralizada da aplicação.

Centraliza variáveis de ambiente e constantes usadas por múltiplas camadas
(CORS, validação de upload da SPEC 0008), evitando leituras de os.getenv
e constantes soltas espalhadas por main.py e pelas rotas.
"""

import os

ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Persistência (SPEC 0004) — usada por app/db/session.py.
# Formato: postgresql://usuario:senha@host:5432/nome_do_banco
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_resume_analyzer",
)

# Feature flag da API de histórico (SPEC 0005) — desligada por padrão.
# Sem autenticação, o histórico é global e anônimo (qualquer cliente vê
# análises de qualquer pessoa); por isso fica desligada em produção até
# existir autenticação/sessão. Testes e CI ligam explicitamente via
# ENABLE_HISTORY_API=true. Aceita "true"/"1"/"yes" (case-insensitive).
ENABLE_HISTORY_API: bool = os.getenv("ENABLE_HISTORY_API", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# Feature flag da API de analytics (SPEC 0006) — desligada por padrão.
# Flag própria, separada de ENABLE_HISTORY_API: analytics expõe apenas
# números agregados (médias, contagens, rankings), nunca um registro
# individual — um perfil de risco diferente do histórico granular. Isso
# permite ligar/desligar as duas capacidades de forma independente no
# deploy. Sem autenticação, os analytics também são globais/anônimos
# (ver PRIVACY.md); por isso permanecem desligados em produção até
# existir autenticação/sessão. Testes e CI ligam via ENABLE_ANALYTICS_API=true.
ENABLE_ANALYTICS_API: bool = os.getenv("ENABLE_ANALYTICS_API", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# Feature flag do matching semântico via embeddings (SPEC 0011) — desligada
# por padrão em todos os ambientes, incluindo produção. A dependência pesada
# (sentence-transformers) fica só em requirements-dev.txt — nunca na imagem
# de produção (ver Dockerfile) — por isso mesmo que a flag seja ligada por
# engano em produção sem a dependência instalada, o fallback (ver
# app/engines/semantic/hybrid.py) garante que /analyze continua funcionando
# normalmente, apenas sem o enriquecimento semântico.
ENABLE_SEMANTIC_MATCHING: bool = os.getenv("ENABLE_SEMANTIC_MATCHING", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# Feature flag do feedback textual via LLM local (SPEC 0014) — desligada por
# padrão em todos os ambientes, incluindo produção. Diferente da SPEC 0011
# (onde o peso era a dependência Python sentence-transformers), aqui o que
# não existe em produção é o próprio processo Ollama — não uma biblioteca
# pesada (httpx, usado para chamá-lo, já está em requirements.txt). Ligar a
# flag sem um Ollama acessível não quebra nada — o fallback (ver
# app/services/llm_feedback_service.py) garante que /analyze continua
# funcionando normalmente, apenas sem os campos de feedback do LLM.
ENABLE_LLM_FEEDBACK: bool = os.getenv("ENABLE_LLM_FEEDBACK", "false").strip().lower() in (
    "true",
    "1",
    "yes",
)

# Provider de LLM ativo (SPEC 0014) — apenas "ollama" é implementado nesta
# Spec. OLLAMA_BASE_URL/OLLAMA_MODEL configuram onde e qual modelo local
# usar; nenhum destes valores é relevante em produção (a flag acima
# permanece false lá).
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1")

# Validação de upload de currículo (SPEC 0008) — valores inalterados
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5 MB em bytes
PDF_MAGIC_BYTES: bytes = b"%PDF-"
ALLOWED_MIME_TYPE: str = "application/pdf"
ALLOWED_EXTENSION: str = ".pdf"


def get_cors_allowed_origins() -> list[str]:
    """
    Retorna as origens permitidas para CORS conforme o ambiente.

    Em desenvolvimento: permite qualquer origem (facilita uso com Vite dev server).
    Em produção: restringe ao domínio do frontend via FRONTEND_ORIGIN.
    """
    if ENVIRONMENT == "development":
        return ["*"]
    return [FRONTEND_ORIGIN]
