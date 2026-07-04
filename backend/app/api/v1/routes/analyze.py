"""
analyze.py — Rota de análise de currículo.

Registrada tanto sem prefixo (rota legada /analyze) quanto sob /api/v1
(rota versionada /api/v1/analyze) a partir da mesma função — ver main.py
e app/api/v1/router.py. Nenhuma lógica é duplicada entre as duas rotas.

Validação de upload delegada a PdfValidationService (SPEC 0008) e
orquestração da análise delegada a AnalysisService — esta rota só
coordena a chamada, sem conter lógica de negócio.

Sessão anônima (SPEC 0009): o header X-Session-Id é opcional aqui — se
ausente ou inválido, get_or_create_session_id() gera um UUID novo. A
análise nunca falha por causa do header; session_id nunca aparece na
resposta (AnalyzeResponse não muda).

Matching semântico (SPEC 0011): response_model_exclude_none=True garante
que semantic_score/hybrid_score/semantic_matches (opcionais, ver
app/domain/schemas/analysis.py) só aparecem no JSON de resposta quando
run_analysis os preenche de fato (ENABLE_SEMANTIC_MATCHING ligada e serviço
de embeddings bem-sucedido) — com a flag desligada, a resposta continua
byte-a-byte idêntica à anterior a esta Spec.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.exceptions import internal_analysis_error
from app.core.session import get_or_create_session_id
from app.domain.schemas.analysis import AnalyzeResponse
from app.services import pdf_validation_service
from app.services.analysis_service import run_analysis

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    response_model_exclude_none=True,
    summary="Analisar currículo",
)
async def analyze_resume(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    job_description: str = Form(..., description="Descrição da vaga"),
    session_id: UUID = Depends(get_or_create_session_id),
):
    """
    Recebe um currículo em PDF e a descrição de uma vaga.
    Retorna score de compatibilidade, skills encontradas,
    skills faltantes e recomendações de melhoria.

    Validações de upload, nesta ordem:
    1. Extensão do arquivo (apenas quando o filename está disponível);
    2. Tipo MIME declarado (content_type);
    3. Descrição da vaga (comprimento);
    4. Arquivo vazio (após leitura dos bytes);
    5. Tamanho do arquivo (após leitura dos bytes);
    6. Magic bytes do PDF (%PDF-).

    Nenhuma mensagem de erro inclui conteúdo do arquivo ou da vaga enviados.

    O header X-Session-Id é opcional (ver SPEC 0009) — se ausente ou
    inválido, um novo é gerado automaticamente e usado apenas para
    persistência; nunca aparece na resposta.
    """
    pdf_validation_service.validate_filename_and_mime(file)
    pdf_validation_service.validate_job_description(job_description)

    try:
        pdf_bytes = await file.read()
    finally:
        await file.close()

    pdf_validation_service.validate_file_bytes(pdf_bytes)

    # Delega toda a análise ao AnalysisService.
    # Captura exceções inesperadas e retorna HTTP 500.
    try:
        result = run_analysis(pdf_bytes, job_description, session_id)
    except HTTPException:
        # Re-lança HTTPExceptions conhecidas sem sobrescrever
        raise
    except Exception:
        raise internal_analysis_error()

    return result
