"""
base.py — Contrato mínimo que um provider de LLM implementa (SPEC 0014).

Apenas Ollama (ollama_provider.py) é implementado nesta Spec — este
Protocol existe só para deixar explícito o formato esperado por
llm_feedback_service.generate_feedback, sem introduzir abstração
especulativa (nenhuma fábrica de providers, nenhum registro dinâmico).
"""

from typing import Protocol


class LLMUnavailableError(Exception):
    """
    Levantada quando o provider de LLM não pode ser usado (processo
    inacessível, timeout, erro HTTP). O chamador (llm_feedback_service)
    trata isso como fallback — nunca deve propagar para analysis_service.
    """


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Envia o prompt ao modelo e retorna o texto bruto da resposta."""
        ...
