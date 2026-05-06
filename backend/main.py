"""
main.py — Entrypoint da aplicação AI Resume Analyzer.

Inicializa o FastAPI, configura CORS e registra as rotas.
"""

import os
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.analyzer import analyze
from app.schemas import AnalyzeResponse

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
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

if ENVIRONMENT == "development":
    allowed_origins = ["*"]
else:
    allowed_origins = [FRONTEND_ORIGIN]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.get("/health", summary="Health check")
def health_check():
    """
    Verifica se o serviço está em execução.
    Retorna {"status": "ok"} com HTTP 200.
    """
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse, summary="Analisar currículo")
async def analyze_resume(
    file: UploadFile = File(..., description="Arquivo PDF do currículo"),
    job_description: str = Form(..., description="Descrição da vaga"),
):
    """
    Recebe um currículo em PDF e a descrição de uma vaga.
    Retorna score de compatibilidade, skills encontradas,
    skills faltantes e recomendações de melhoria.
    """
    # ---------------------------------------------------------------------------
    # Validação 1: tipo do arquivo — deve ser application/pdf
    # ---------------------------------------------------------------------------
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=422,
            detail="O arquivo enviado não é um PDF válido. Envie um arquivo com extensão .pdf.",
        )

    # ---------------------------------------------------------------------------
    # Validação 2: comprimento da descrição da vaga (10–10.000 caracteres)
    # ---------------------------------------------------------------------------
    if len(job_description.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="A descrição da vaga deve ter pelo menos 10 caracteres.",
        )
    if len(job_description) > 10_000:
        raise HTTPException(
            status_code=422,
            detail="A descrição da vaga excede o limite de 10.000 caracteres.",
        )

    # ---------------------------------------------------------------------------
    # Lê os bytes do arquivo e valida o tamanho (≤ 5 MB)
    # ---------------------------------------------------------------------------
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB em bytes

    try:
        pdf_bytes = await file.read()
    finally:
        await file.close()

    # Validação 3: tamanho do arquivo após leitura
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Arquivo excede o tamanho máximo permitido de 5 MB.",
        )

    # Delega toda a análise ao Analyzer (único orquestrador)
    # Captura exceções inesperadas e retorna HTTP 500
    try:
        result = analyze(pdf_bytes, job_description)
    except HTTPException:
        # Re-lança HTTPExceptions conhecidas sem sobrescrever
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Erro interno durante a análise. Tente novamente.",
        )

    return result
