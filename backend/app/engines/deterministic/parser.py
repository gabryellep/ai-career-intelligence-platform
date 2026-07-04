"""
parser.py — Extração de texto de arquivos PDF.

Utiliza PyMuPDF (fitz) para extrair o conteúdo textual de todas as páginas
de um PDF recebido como bytes.

Decisão de design:
- PyMuPDF foi escolhido por ser rápido, não exigir dependências externas
  do sistema operacional e suportar a maioria dos PDFs gerados por
  editores de texto.
- PDFs baseados em imagem (sem camada de texto) retornam string vazia.
  OCR está fora do escopo da v1.
"""

import fitz  # PyMuPDF


def extract_text(pdf_bytes: bytes) -> str:
    """
    Extrai o texto de todas as páginas de um PDF.

    Args:
        pdf_bytes: Conteúdo do arquivo PDF em bytes.

    Returns:
        String com o texto extraído de todas as páginas, separadas por
        espaço em branco. Retorna string vazia se o PDF não contiver
        texto extraível ou se os bytes forem inválidos.
    """
    try:

        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            pages_text = []
            for page in document:
                # Extrai o texto de cada página
                page_text = page.get_text()
                if page_text.strip():
                    pages_text.append(page_text)

        # Junta o texto de todas as páginas
        return "\n".join(pages_text)

    except Exception:
        # Retorna string vazia para bytes inválidos ou PDFs corrompidos
        return ""
