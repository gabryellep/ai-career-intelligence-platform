"""
ollama_provider.py — Provider de LLM via Ollama local (SPEC 0014).

Fala apenas HTTP (via httpx, já em requirements.txt — nenhuma dependência
nova) com um processo Ollama rodando localmente (OLLAMA_BASE_URL). Não
entende o domínio da aplicação (score, skills etc.) — isso é
responsabilidade exclusiva de app.services.llm_feedback_service, que monta
o prompt e valida a resposta. Este módulo só sabe fazer a chamada HTTP e
traduzir falhas de rede/timeout em LLMUnavailableError.

Nunca chamado em CI nem em produção (ENABLE_LLM_FEEDBACK=false por
padrão) — Ollama é um processo externo que só existe no ambiente local de
quem ligar a flag deliberadamente.
"""

import httpx

from app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.services.llm_providers.base import LLMUnavailableError

# Timeout fixo (SPEC 0014, decisão aprovada) — modelos locais em CPU podem
# ser lentos; 20s equilibra dar tempo real ao modelo sem pendurar /analyze
# indefinidamente.
REQUEST_TIMEOUT_SECONDS = 20.0


def generate(prompt: str) -> str:
    """
    Envia o prompt ao Ollama (endpoint /api/generate, sem streaming) e
    retorna o texto bruto da resposta.

    Levanta LLMUnavailableError em qualquer falha de rede, timeout ou
    status HTTP de erro — nunca deixa uma exceção de httpx escapar
    diretamente, para que o chamador trate uniformemente como fallback.
    """
    try:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMUnavailableError("Falha ao chamar o Ollama") from exc

    try:
        payload = response.json()
        return payload["response"]
    except (ValueError, KeyError) as exc:
        raise LLMUnavailableError("Resposta do Ollama em formato inesperado") from exc
