"""
test_parser.py — Testes unitários do módulo parser.py.

Testa a função extract_text com três cenários:
1. PDF válido contendo texto — deve retornar o texto extraído
2. Bytes inválidos — deve retornar string vazia sem lançar exceção
3. PDF sem texto extraível — deve retornar string vazia sem lançar exceção

Os testes criam PDFs programaticamente usando PyMuPDF para não depender
de arquivos externos.
"""

import fitz  # PyMuPDF
import pytest
from app.parser import extract_text


def create_pdf_with_text(text: str) -> bytes:
    """
    Cria um PDF simples em memória contendo o texto fornecido.
    Usado para gerar fixtures de teste sem depender de arquivos externos.
    """
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 100), text)
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def create_empty_pdf() -> bytes:
    """
    Cria um PDF válido mas sem nenhum texto (página em branco).
    Simula um PDF baseado em imagem sem camada de texto.
    """
    document = fitz.open()
    document.new_page()  # página em branco, sem texto
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def test_extract_text_from_valid_pdf():
    """PDF válido com texto deve retornar o texto extraído."""
    expected_text = "Python FastAPI Docker"
    pdf_bytes = create_pdf_with_text(expected_text)

    result = extract_text(pdf_bytes)

    assert isinstance(result, str)
    assert len(result) > 0
    assert "Python" in result
    assert "FastAPI" in result
    assert "Docker" in result


def test_extract_text_returns_string_type():
    """O retorno deve sempre ser uma string, independente da entrada."""
    pdf_bytes = create_pdf_with_text("Teste")
    result = extract_text(pdf_bytes)
    assert isinstance(result, str)


def test_extract_text_with_invalid_bytes():
    """Bytes inválidos devem retornar string vazia sem lançar exceção."""
    result = extract_text(b"isso nao e um pdf valido")
    assert result == ""


def test_extract_text_with_empty_bytes():
    """Bytes vazios devem retornar string vazia sem lançar exceção."""
    result = extract_text(b"")
    assert result == ""


def test_extract_text_from_empty_pdf():
    """PDF válido sem texto (página em branco) deve retornar string vazia."""
    pdf_bytes = create_empty_pdf()
    result = extract_text(pdf_bytes)
    assert result == ""


def test_extract_text_does_not_raise_on_invalid_input():
    """A função nunca deve lançar exceção, independente da entrada."""
    try:
        extract_text(b"dados corrompidos")
        extract_text(b"")
        extract_text(b"\x00\x01\x02\x03")
    except Exception as e:
        pytest.fail(f"extract_text lançou exceção inesperada: {e}")
