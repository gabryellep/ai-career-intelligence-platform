"""
session.py — Extração/validação do header X-Session-Id (SPEC 0009).

Sessão anônima: um UUID gerado no frontend (localStorage), enviado neste
header, usado para isolar histórico/analytics por "sessão de navegador".
Não identifica uma pessoa e não é um mecanismo de autenticação real —
apenas posse do UUID já concede acesso aos dados daquela sessão.

Dois padrões de uso, por criticidade (ver SPEC 0009, decisão técnica):
    - POST /analyze: usa get_or_create_session_id() abaixo — header
      ausente ou inválido nunca bloqueia a análise, um UUID novo é
      gerado automaticamente.
    - Rotas de leitura (histórico/analytics): usam diretamente
      `session_id: UUID = Header(..., alias="X-Session-Id")` como
      parâmetro de rota — o FastAPI/Pydantic validam formato e
      obrigatoriedade, retornando 422 automaticamente se ausente ou
      malformado.
"""

from uuid import UUID, uuid4

from fastapi import Header


def get_or_create_session_id(
    x_session_id: str | None = Header(None, alias="X-Session-Id"),
) -> UUID:
    """
    Usada exclusivamente por POST /analyze. Se o header vier ausente ou
    não for um UUID válido, gera um novo automaticamente — a análise
    nunca falha por causa do formato/ausência do header.
    """
    if x_session_id:
        try:
            return UUID(x_session_id)
        except ValueError:
            pass
    return uuid4()
