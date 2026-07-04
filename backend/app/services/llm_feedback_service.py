"""
llm_feedback_service.py — Camada de serviço do feedback textual via LLM (SPEC 0014).

Orquestra: monta um prompt curto a partir de dados já estruturados da
análise (nunca texto bruto do usuário), chama o provider configurado, e
valida a resposta antes de aceitar qualquer campo. Chamado por
app.services.analysis_service.run_analysis — nunca pela rota HTTP
diretamente, nem pelo motor determinístico/semântico (que não devem
conhecer LLM/HTTP).

Contrato de dados enviados ao LLM (nunca mais que isso — ver SPEC 0014):
score, matched_skills, missing_skills, partial_skills, extra_skills,
insights (strengths/weaknesses), semantic_score/hybrid_score (se
existirem no resultado). Nunca PDF, texto bruto, hashes ou session_id —
essas chaves nem existem no dicionário `result` recebido aqui (ver
app/engines/deterministic/analyzer.py e app/services/analysis_service.py).

O LLM apenas explica o resultado já calculado — nunca decide score,
matching ou classificação. generate_feedback nunca altera `result`; apenas
lê dele e retorna um dicionário novo e separado.
"""

import json

from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import LLM_PROVIDER
from app.services.llm_providers.base import LLMUnavailableError
from app.services.llm_providers.ollama_provider import generate as ollama_generate

# Limite de itens por lista (SPEC 0014, decisão aprovada) — protege contra
# respostas verbosas do modelo, mesmo padrão já usado em
# insights.strengths/weaknesses/priority_actions.
MAX_LIST_ITEMS = 5

_SUPPORTED_PROVIDERS = {"ollama": ollama_generate}


class _LLMFeedbackPayload(BaseModel):
    """
    Schema de validação da resposta do LLM — interno a este módulo, nunca
    exposto publicamente (não é o mesmo modelo de app.domain.schemas.analysis).

    extra="ignore" (decisão aprovada): campos extras que o modelo incluir na
    resposta são descartados, sem invalidar o restante. Os 4 campos abaixo
    são obrigatórios com o tipo correto — qualquer um ausente ou de tipo
    errado invalida a resposta inteira (ValidationError, tratado como
    fallback pelo chamador).
    """

    model_config = ConfigDict(extra="ignore")

    llm_summary: str
    llm_improvement_plan: list[str]
    llm_study_suggestions: list[str]
    llm_resume_tips: list[str]


def _build_prompt(result: dict) -> str:
    """
    Monta o prompt inteiramente a partir de dados já estruturados do
    resultado da análise — nunca concatenação de texto livre do usuário.
    """
    insights = result.get("insights", {})

    lines = [
        "Você é um assistente que explica o resultado de uma análise automática "
        "de compatibilidade entre um currículo e uma vaga. Use APENAS as "
        "informações abaixo — não invente skills, experiências ou fatos que "
        "não estejam listados.",
        "",
        "Dados da análise:",
        f"- Score de compatibilidade: {result.get('score', 0)}/100",
        f"- Skills que o candidato tem e a vaga pede: {result.get('matched_skills', [])}",
        f"- Skills que a vaga pede e o candidato não tem: {result.get('missing_skills', [])}",
        f"- Skills parcialmente atendidas: {result.get('partial_skills', [])}",
        f"- Skills extras do candidato (não pedidas pela vaga): {result.get('extra_skills', [])}",
        f"- Pontos fortes identificados: {insights.get('strengths', [])}",
        f"- Pontos de atenção identificados: {insights.get('weaknesses', [])}",
    ]

    if "semantic_score" in result:
        lines.append(f"- Score semântico (aproximações via embeddings): {result['semantic_score']}/100")
    if "hybrid_score" in result:
        lines.append(f"- Score híbrido (determinístico + semântico): {result['hybrid_score']}/100")

    lines += [
        "",
        "Responda APENAS com um objeto JSON válido, sem texto antes ou depois, no formato:",
        "{",
        '  "llm_summary": "um parágrafo curto (2-4 frases) resumindo o resultado",',
        '  "llm_improvement_plan": ["passo 1", "passo 2", "..."],',
        '  "llm_study_suggestions": ["sugestão 1", "..."],',
        '  "llm_resume_tips": ["dica 1", "..."]',
        "}",
        "",
        "Regras obrigatórias:",
        "- Nunca prometa emprego, contratação, aprovação ou qualquer resultado garantido.",
        "- Use apenas as skills listadas acima — não mencione tecnologias que não estejam na lista.",
        "- Seja direto e prático, sem floreios.",
    ]

    return "\n".join(lines)


def generate_feedback(result: dict, generate_fn=None) -> dict | None:
    """
    Gera feedback textual a partir do resultado já calculado da análise.

    Retorna None em qualquer falha (provider não suportado, Ollama
    inacessível/timeout, resposta não é JSON válido, resposta não bate com
    o schema esperado) — o chamador (analysis_service.run_analysis) deve
    tratar None como "sem feedback", nunca propagar exceção.

    generate_fn é injetável para testes — evita depender de um Ollama real.
    """
    if generate_fn is None:
        generate_fn = _SUPPORTED_PROVIDERS.get(LLM_PROVIDER)

    if generate_fn is None:
        return None

    prompt = _build_prompt(result)

    try:
        raw_response = generate_fn(prompt)
    except LLMUnavailableError:
        return None
    except Exception:
        return None

    try:
        parsed = json.loads(raw_response)
        payload = _LLMFeedbackPayload.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None

    return {
        "llm_summary": payload.llm_summary,
        "llm_improvement_plan": payload.llm_improvement_plan[:MAX_LIST_ITEMS],
        "llm_study_suggestions": payload.llm_study_suggestions[:MAX_LIST_ITEMS],
        "llm_resume_tips": payload.llm_resume_tips[:MAX_LIST_ITEMS],
    }
