"""
test_routes.py — Testes de integração das rotas da API.

Testa as rotas GET /health e POST /analyze usando TestClient do FastAPI.
Os PDFs são criados programaticamente com PyMuPDF.
"""

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_pdf_with_text(text: str) -> bytes:
    """Cria um PDF simples em memória com o texto fornecido."""
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 100), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def create_empty_pdf() -> bytes:
    """Cria um PDF válido sem texto."""
    document = fitz.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


# Descrição de vaga válida (≥ 50 caracteres)
VALID_JOB = (
    "Buscamos desenvolvedor Python com experiência em FastAPI, Docker e AWS. "
    "Conhecimento em machine learning é um diferencial."
)


# ---------------------------------------------------------------------------
# Testes: GET /health
# ---------------------------------------------------------------------------

def test_health_check_returns_200():
    """GET /health deve retornar HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_status_ok():
    """GET /health deve retornar {"status": "ok"}."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Testes: POST /analyze — casos de sucesso
# ---------------------------------------------------------------------------

def test_analyze_with_valid_pdf_returns_200():
    """POST /analyze com PDF válido deve retornar HTTP 200."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker machine learning")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 200


def test_analyze_response_has_required_fields():
    """POST /analyze deve retornar JSON com as 4 chaves obrigatórias."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "score" in data
    assert "matched_skills" in data
    assert "missing_skills" in data
    assert "recommendations" in data


def test_analyze_score_in_valid_range():
    """O score retornado deve estar entre 0 e 100."""
    pdf_bytes = create_pdf_with_text("Python FastAPI Docker")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert 0 <= data["score"] <= 100


# ---------------------------------------------------------------------------
# Testes: POST /analyze — validações (erros esperados)
# ---------------------------------------------------------------------------

def test_analyze_with_non_pdf_file_returns_422():
    """Arquivo não-PDF deve retornar HTTP 422."""
    txt_content = b"Isso nao e um PDF"

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.txt", txt_content, "text/plain")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 422


def test_analyze_with_non_pdf_returns_descriptive_message():
    """Arquivo não-PDF deve retornar mensagem de erro descritiva."""
    response = client.post(
        "/analyze",
        files={"file": ("curriculo.txt", b"texto", "text/plain")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) > 0


def test_analyze_with_short_job_description_returns_422():
    """Descrição da vaga com menos de 50 caracteres deve retornar HTTP 422."""
    pdf_bytes = create_pdf_with_text("Python")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": "Python"},  # menos de 50 chars
    )

    assert response.status_code == 422


def test_analyze_with_short_job_description_returns_correct_message():
    """Descrição curta deve retornar a mensagem correta."""
    pdf_bytes = create_pdf_with_text("Python")

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": "Curto"},
    )

    data = response.json()
    assert "10 caracteres" in data["detail"]


def test_analyze_with_long_job_description_returns_422():
    """Descrição da vaga com mais de 10.000 caracteres deve retornar HTTP 422."""
    pdf_bytes = create_pdf_with_text("Python")
    long_description = "a" * 10_001

    response = client.post(
        "/analyze",
        files={"file": ("curriculo.pdf", pdf_bytes, "application/pdf")},
        data={"job_description": long_description},
    )

    assert response.status_code == 422


def test_analyze_with_oversized_file_returns_413():
    """Arquivo maior que 5 MB deve retornar HTTP 413."""
    # Cria conteúdo com mais de 5 MB
    oversized_content = b"%PDF-1.4" + b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/analyze",
        files={"file": ("grande.pdf", oversized_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    assert response.status_code == 413


def test_analyze_with_oversized_file_returns_correct_message():
    """Arquivo > 5 MB deve retornar a mensagem correta."""
    oversized_content = b"%PDF-1.4" + b"x" * (5 * 1024 * 1024 + 1)

    response = client.post(
        "/analyze",
        files={"file": ("grande.pdf", oversized_content, "application/pdf")},
        data={"job_description": VALID_JOB},
    )

    data = response.json()
    assert "5 MB" in data["detail"]
