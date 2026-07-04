"""
hybrid.py — Combina o matching determinístico com uma camada semântica
opcional (SPEC 0011).

Chamado apenas quando app.core.config.ENABLE_SEMANTIC_MATCHING é True.
Nunca altera match_details nem o score determinístico (matcher.py) — apenas
calcula campos adicionais (semantic_score, hybrid_score, semantic_matches)
a partir das skills que o motor determinístico já classificou como
"missing". Skills "matched"/"partial" não passam por aqui — o
determinístico já resolveu essas.
"""

from app.engines.semantic.embedding_service import EmbeddingUnavailableError, compute_similarity

# Pesos do score híbrido (SPEC 0011, decisão aprovada) — fixos, não
# configuráveis por variável de ambiente.
DETERMINISTIC_WEIGHT = 0.7
SEMANTIC_WEIGHT = 0.3

# Similaridade mínima (cosseno) para considerar um match semântico válido.
#
# Calibrado na SPEC 0013 (era 0.70, definido sem evidência empírica na SPEC
# 0011). Uma amostra de 27 pares positivos + 17 negativos, rodada com o
# modelo real all-MiniLM-L6-v2 (backend/scripts/semantic_calibration.py),
# mostrou 0 falsos positivos em TODOS os thresholds candidatos testados
# (0.50 a 0.70) — o par negativo com maior similaridade observada foi
# "java"/"javascript" em 0.40, uma margem de 0.10 abaixo de 0.50. Como
# reduzir o threshold não introduziu nenhum falso positivo na amostra, mas
# dobrou o recall (0.07 -> 0.33 *) e o F1 (0.14 -> 0.50), o valor foi
# atualizado para 0.50 — o menor threshold testado, e o de melhor F1 entre
# os candidatos avaliados. Ver backend/scripts/semantic_calibration_output.md
# para a tabela completa de métricas por threshold.
SEMANTIC_SIMILARITY_THRESHOLD = 0.50

# Limite de itens retornados em semantic_matches (decisão aprovada) — não
# limita a contagem usada no cálculo de semantic_score, apenas a lista
# exibida.
MAX_SEMANTIC_MATCHES = 10


def enrich_with_semantic_matching(skill_match: dict, score: int, similarity_fn=compute_similarity) -> dict | None:
    """
    Calcula semantic_score, hybrid_score e semantic_matches a partir do
    resultado do matching determinístico (skill_match, ver
    app.engines.deterministic.matcher.analyze_skill_match) e do score
    determinístico já calculado.

    Retorna None em caso de falha do serviço de embeddings (dependência
    ausente, erro ao carregar o modelo, erro durante a inferência) — o
    chamador (analyzer.py) deve tratar None como "sem enriquecimento
    semântico" e omitir os três campos do resultado, nunca propagar erro.

    similarity_fn é injetável para testes — evita depender do modelo real.
    """
    matched = list(skill_match.get("matched", []))
    partial = list(skill_match.get("partial", []))
    missing = list(skill_match.get("missing", []))
    extra = list(skill_match.get("extra", []))

    total_required = len(matched) + len(partial) + len(missing)

    if total_required == 0 or not missing or not extra:
        # Nada para aproximar semanticamente (vaga sem skills exigidas, sem
        # gaps, ou currículo sem skills extras para comparar) — score
        # semântico coincide com o determinístico.
        semantic_score = score
        hybrid_score = _combine(score, semantic_score)
        return {"semantic_score": semantic_score, "hybrid_score": hybrid_score, "semantic_matches": []}

    semantic_hits: list[dict] = []
    try:
        for job_skill in missing:
            best_match = None
            best_similarity = 0.0
            for resume_skill in extra:
                similarity = similarity_fn(job_skill, resume_skill)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = resume_skill

            if best_match is not None and best_similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
                semantic_hits.append(
                    {
                        "job_skill": job_skill,
                        "matched_resume_skill": best_match,
                        "similarity": round(best_similarity, 2),
                    }
                )
    except EmbeddingUnavailableError:
        return None
    except Exception:
        return None

    semantic_hits.sort(key=lambda item: item["similarity"], reverse=True)
    semantic_matches = semantic_hits[:MAX_SEMANTIC_MATCHES]

    # semantic_score usa a mesma fórmula de peso do score determinístico
    # (matched=1.0, partial=0.5), tratando cada match semântico como um
    # "partial" adicional (peso 0.5) — reflete que a aproximação semântica
    # é uma evidência mais fraca que um match exato por regra.
    points = len(matched) * 1.0 + len(partial) * 0.5 + len(semantic_hits) * 0.5
    semantic_score = min(100, round((points / total_required) * 100))

    hybrid_score = _combine(score, semantic_score)

    return {
        "semantic_score": semantic_score,
        "hybrid_score": hybrid_score,
        "semantic_matches": semantic_matches,
    }


def _combine(score: int, semantic_score: int) -> int:
    hybrid = round(DETERMINISTIC_WEIGHT * score + SEMANTIC_WEIGHT * semantic_score)
    return max(0, min(100, hybrid))
