"""
exceptions.py — Helpers de erro HTTP usados pelas rotas da API.

Centraliza as mensagens de erro já validadas pela SPEC 0008, evitando
strings duplicadas entre serviços e rotas. Nenhuma mensagem inclui
conteúdo do arquivo ou da descrição da vaga enviados pelo usuário.

Os status codes e textos abaixo são idênticos aos usados antes da
reorganização em camadas (SPEC 0001) — apenas centralizados.
"""

from fastapi import HTTPException


def invalid_pdf_error() -> HTTPException:
    """Extensão ou tipo MIME do arquivo não correspondem a um PDF."""
    return HTTPException(
        status_code=422,
        detail="O arquivo enviado não é um PDF válido. Envie um arquivo com extensão .pdf.",
    )


def job_description_too_short_error() -> HTTPException:
    """Descrição da vaga com menos de 10 caracteres."""
    return HTTPException(
        status_code=422,
        detail="A descrição da vaga deve ter pelo menos 10 caracteres.",
    )


def job_description_too_long_error() -> HTTPException:
    """Descrição da vaga acima de 10.000 caracteres."""
    return HTTPException(
        status_code=422,
        detail="A descrição da vaga excede o limite de 10.000 caracteres.",
    )


def empty_file_error() -> HTTPException:
    """Arquivo enviado com 0 bytes."""
    return HTTPException(
        status_code=422,
        detail="O arquivo enviado está vazio.",
    )


def file_too_large_error() -> HTTPException:
    """Arquivo acima do tamanho máximo permitido (5 MB)."""
    return HTTPException(
        status_code=413,
        detail="Arquivo excede o tamanho máximo permitido de 5 MB.",
    )


def invalid_pdf_signature_error() -> HTTPException:
    """Conteúdo do arquivo não começa com a assinatura binária de um PDF (%PDF-)."""
    return HTTPException(
        status_code=422,
        detail="O arquivo enviado não parece ser um PDF válido.",
    )


def internal_analysis_error() -> HTTPException:
    """Erro inesperado durante a análise — nunca expõe detalhes da exceção original."""
    return HTTPException(
        status_code=500,
        detail="Erro interno durante a análise. Tente novamente.",
    )
