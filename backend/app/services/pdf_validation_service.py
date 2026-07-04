"""
pdf_validation_service.py — Validações de segurança de upload de currículo (SPEC 0008).

Centraliza a lógica antes definida inline em main.py: extensão, tipo MIME,
descrição da vaga, arquivo vazio, tamanho máximo e magic bytes. A ordem de
validação e as mensagens de erro são preservadas exatamente como definidas
na SPEC 0008 — esta reorganização apenas move o código de lugar.

Ordem de validação esperada pela rota que consome este serviço:
    1. validate_filename_and_mime(file)
    2. validate_job_description(job_description)
    3. (leitura dos bytes do arquivo)
    4. validate_file_bytes(pdf_bytes)
"""

from fastapi import UploadFile

from app.core import config
from app.core.exceptions import (
    empty_file_error,
    file_too_large_error,
    invalid_pdf_error,
    invalid_pdf_signature_error,
    job_description_too_long_error,
    job_description_too_short_error,
)


def validate_filename_and_mime(file: UploadFile) -> None:
    """
    Valida extensão do arquivo (apenas quando o filename está disponível)
    e o tipo MIME declarado. Nenhuma das duas é a única barreira de
    segurança — magic bytes e tamanho seguem sendo validados depois.
    """
    if file.filename and not file.filename.lower().endswith(config.ALLOWED_EXTENSION):
        raise invalid_pdf_error()

    if file.content_type != config.ALLOWED_MIME_TYPE:
        raise invalid_pdf_error()


def validate_job_description(job_description: str) -> None:
    """Valida o comprimento da descrição da vaga (10–10.000 caracteres)."""
    if len(job_description.strip()) < 10:
        raise job_description_too_short_error()
    if len(job_description) > 10_000:
        raise job_description_too_long_error()


def validate_file_bytes(pdf_bytes: bytes) -> None:
    """
    Valida arquivo vazio, tamanho máximo e magic bytes, nesta ordem
    (após a leitura dos bytes do arquivo).
    """
    if len(pdf_bytes) == 0:
        raise empty_file_error()

    if len(pdf_bytes) > config.MAX_FILE_SIZE:
        raise file_too_large_error()

    if not pdf_bytes.startswith(config.PDF_MAGIC_BYTES):
        raise invalid_pdf_signature_error()
