"""
embedding_service.py — Serviço de embeddings semânticos (SPEC 0011).

O import de sentence-transformers é sempre lazy (dentro de função) e
protegido por try/except: o pacote só existe em requirements-dev.txt —
nunca na imagem de produção (ver backend/Dockerfile, que instala apenas
requirements.txt) — então este módulo precisa se comportar de forma
previsível (levantando EmbeddingUnavailableError, nunca um crash de import
não tratado) mesmo quando a dependência não está instalada.

Embeddings são calculados apenas sobre nomes de skills (strings curtas,
ex. "docker", "machine learning") — nunca sobre o texto do currículo ou da
vaga. Os vetores calculados nunca são persistidos em nenhum lugar; apenas a
similaridade final (um float) chega ao chamador.
"""

import math

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


class EmbeddingUnavailableError(Exception):
    """
    Levantada quando o modelo de embeddings não pode ser carregado ou usado
    (dependência ausente, falha ao baixar/carregar pesos, ou erro durante a
    inferência). O chamador (app/engines/semantic/hybrid.py) trata isso como
    fallback — nunca deve propagar para analyzer.py sem tratamento.
    """


def _get_model():
    """Carrega e cacheia (singleton em memória do processo) o modelo de embeddings."""
    global _model
    if _model is not None:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingUnavailableError("sentence-transformers não está instalado") from exc

    try:
        _model = SentenceTransformer(MODEL_NAME)
    except Exception as exc:
        raise EmbeddingUnavailableError("Falha ao carregar o modelo de embeddings") from exc

    return _model


def compute_similarity(term_a: str, term_b: str) -> float:
    """
    Calcula a similaridade de cosseno (0.0 a 1.0) entre os embeddings de duas
    strings curtas (nomes de skills).

    Levanta EmbeddingUnavailableError se o modelo não puder ser carregado ou
    usado — o chamador é responsável por tratar isso como fallback.
    """
    model = _get_model()

    try:
        embeddings = model.encode([term_a, term_b])
    except Exception as exc:
        raise EmbeddingUnavailableError("Falha ao calcular embeddings") from exc

    return _cosine_similarity(embeddings[0], embeddings[1])


def _cosine_similarity(vec_a, vec_b) -> float:
    """
    Cosseno calculado em Python puro (sem numpy) — os vetores retornados por
    sentence-transformers têm poucas centenas de posições, então o custo é
    desprezível, e evita introduzir numpy como dependência própria deste
    módulo (já vem transitivamente com sentence-transformers quando presente).
    """
    dot_product = float(sum(a * b for a, b in zip(vec_a, vec_b)))
    norm_a = math.sqrt(float(sum(a * a for a in vec_a)))
    norm_b = math.sqrt(float(sum(b * b for b in vec_b)))
    denom = norm_a * norm_b
    if denom == 0.0:
        return 0.0
    return float(dot_product / denom)
