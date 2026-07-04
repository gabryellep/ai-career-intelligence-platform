"""
analysis_service.py — Camada de orquestração da análise de compatibilidade.

Camada fina entre a rota HTTP e o motor determinístico: delega toda a
lógica de análise para app.engines.deterministic.analyzer.analyze, sem
duplicar ou alterar o comportamento existente.

Persistência (SPEC 0004): após obter o resultado do motor, esta camada
tenta persistir a análise via AnalysisRepository. O motor determinístico
nunca importa nada de app/db — só esta camada conhece banco de dados.

Resiliência (decisão explícita da SPEC 0004): se a persistência falhar
por qualquer motivo (banco indisponível, erro de schema etc.), a falha é
logada (apenas o tipo da exceção, nunca a mensagem crua nem dados do
usuário) e SILENCIADA — o resultado da análise já computado é sempre
retornado ao chamador. A funcionalidade central do produto (analisar o
currículo) não pode depender da disponibilidade do banco nesta fase.

Isolamento por sessão (SPEC 0009): run_analysis recebe session_id (gerado
pela rota — ver app/api/v1/routes/analyze.py — a partir do header
X-Session-Id, ou automaticamente se ausente/inválido) e o repassa a
save_analysis. session_id nunca é exposto no retorno de run_analysis —
o contrato de AnalyzeResponse não muda.

Feedback via LLM (SPEC 0014): se ENABLE_LLM_FEEDBACK estiver ligada, esta
camada chama llm_feedback_service.generate_feedback com o resultado já
calculado (nunca com PDF/texto bruto/hashes/session_id — esses nunca fazem
parte de `result`). O motor determinístico/semântico não conhece LLM; o
LLM só lê o resultado, nunca o altera. Qualquer falha (Ollama indisponível,
timeout, resposta inválida) é contida aqui e resulta apenas na ausência
dos campos `llm_*` — nunca em erro para o chamador.
"""

from uuid import UUID

from app.core.config import ENABLE_LLM_FEEDBACK
from app.db.session import get_session
from app.engines.deterministic.analyzer import analyze
from app.repositories.analysis_repository import save_analysis
from app.services.llm_feedback_service import generate_feedback


def run_analysis(pdf_bytes: bytes, job_description: str, session_id: UUID, debug: bool = False) -> dict:
    """
    Executa a análise completa de compatibilidade entre currículo e vaga
    e tenta persistir o resultado (sem quebrar em caso de falha de banco).

    Args:
        pdf_bytes: Conteúdo do arquivo PDF do currículo em bytes.
        job_description: Texto da descrição da vaga.
        session_id: Identificador de sessão anônima (SPEC 0009), usado
            apenas para isolar o histórico/analytics — nunca exposto na
            resposta.
        debug: Se True (apenas em desenvolvimento), inclui 'resume_text_preview'.

    Returns:
        Dicionário com o resultado da análise (score, matched_skills,
        missing_skills, partial_skills, extra_skills, match_details,
        recommendations, insights) — idêntico ao contrato anterior à
        SPEC 0004; nenhum campo interno de persistência é exposto aqui.
    """
    result = analyze(pdf_bytes, job_description, debug=debug)

    # Metadados internos calculados pelo motor (ver analyzer.py) — nunca
    # fazem parte do contrato público, removidos antes de retornar.
    resume_text_sha256 = result.pop("_resume_text_sha256", None)
    resume_text_length = result.pop("_resume_text_length", 0)

    if ENABLE_LLM_FEEDBACK:
        llm_result = _try_llm_feedback(result)
        if llm_result is not None:
            result["llm_summary"] = llm_result["llm_summary"]
            result["llm_improvement_plan"] = llm_result["llm_improvement_plan"]
            result["llm_study_suggestions"] = llm_result["llm_study_suggestions"]
            result["llm_resume_tips"] = llm_result["llm_resume_tips"]

    _persist_analysis(pdf_bytes, job_description, resume_text_sha256, resume_text_length, result, session_id)

    return result


def _try_llm_feedback(result: dict) -> dict | None:
    """
    Chama llm_feedback_service.generate_feedback, contendo qualquer exceção
    inesperada — nunca propaga para run_analysis. Retorna None em caso de
    qualquer falha; loga apenas o tipo da exceção.
    """
    try:
        return generate_feedback(result)
    except Exception as e:
        print(f"Erro ao gerar feedback via LLM: {type(e).__name__}")
        return None


def _persist_analysis(
    pdf_bytes: bytes,
    job_description: str,
    resume_text_sha256: str | None,
    resume_text_length: int,
    result: dict,
    session_id: UUID,
) -> None:
    """Persiste a análise; falhas de banco são logadas e nunca propagadas."""
    try:
        with get_session() as db:
            save_analysis(db, pdf_bytes, job_description, resume_text_sha256, resume_text_length, result, session_id)
    except Exception as e:
        # Nunca loga a mensagem crua da exceção nem dados do usuário —
        # apenas o tipo, seguindo o mesmo padrão da SPEC 0008/0001.
        print(f"Erro ao persistir análise: {type(e).__name__}")
