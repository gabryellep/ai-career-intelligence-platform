"""
test_hybrid_matching.py — Testes de app.engines.semantic.hybrid (SPEC 0011).

Usa uma função de similaridade injetada (mock/stub) — nunca depende do
modelo real de embeddings, seguindo a decisão de não baixar o modelo em CI.
"""

from app.engines.semantic.embedding_service import EmbeddingUnavailableError
from app.engines.semantic.hybrid import (
    MAX_SEMANTIC_MATCHES,
    SEMANTIC_SIMILARITY_THRESHOLD,
    enrich_with_semantic_matching,
)


def _similarity_table(table: dict[tuple[str, str], float]):
    """Stub de similarity_fn que consulta uma tabela fixa (para testes determinísticos)."""

    def _fn(term_a: str, term_b: str) -> float:
        return table.get((term_a, term_b), 0.0)

    return _fn


def test_no_missing_skills_semantic_score_equals_deterministic_score():
    """Sem skills 'missing', não há nada para aproximar — semantic_score == score."""
    skill_match = {"matched": ["python", "docker"], "partial": [], "missing": [], "extra": ["kubernetes"]}

    result = enrich_with_semantic_matching(skill_match, score=100, similarity_fn=_similarity_table({}))

    assert result["semantic_score"] == 100
    assert result["hybrid_score"] == 100
    assert result["semantic_matches"] == []


def test_no_extra_skills_semantic_score_equals_deterministic_score():
    """Sem skills 'extra' no currículo, não há candidato para aproximar — sem enriquecimento."""
    skill_match = {"matched": ["python"], "partial": [], "missing": ["aws"], "extra": []}

    result = enrich_with_semantic_matching(skill_match, score=50, similarity_fn=_similarity_table({}))

    assert result["semantic_score"] == 50
    assert result["hybrid_score"] == 50
    assert result["semantic_matches"] == []


def test_semantic_match_above_threshold_increases_semantic_score():
    """Uma aproximação semântica acima do threshold conta como 0.5 ponto extra."""
    skill_match = {"matched": ["python"], "partial": [], "missing": ["machine learning"], "extra": ["ml"]}
    similarity_fn = _similarity_table({("machine learning", "ml"): 0.85})

    result = enrich_with_semantic_matching(skill_match, score=50, similarity_fn=similarity_fn)

    # matched(1) + missing(1) = total_required 2; points = 1.0 (matched) + 0.5 (semantic hit) = 1.5
    # semantic_score = round(1.5 / 2 * 100) = 75
    assert result["semantic_score"] == 75
    assert result["semantic_matches"] == [
        {"job_skill": "machine learning", "matched_resume_skill": "ml", "similarity": 0.85}
    ]
    # hybrid_score = round(0.7 * 50 + 0.3 * 75) = round(35 + 22.5) = round(57.5) = 58
    assert result["hybrid_score"] == 58


def test_semantic_match_below_threshold_is_ignored():
    """Similaridade abaixo do threshold não conta como match semântico."""
    skill_match = {"matched": [], "partial": [], "missing": ["aws"], "extra": ["marketing"]}
    similarity_fn = _similarity_table({("aws", "marketing"): 0.2})

    result = enrich_with_semantic_matching(skill_match, score=0, similarity_fn=similarity_fn)

    assert result["semantic_matches"] == []
    assert result["semantic_score"] == 0
    assert result["hybrid_score"] == 0


def test_semantic_match_exactly_at_threshold_counts():
    """Similaridade igual ao threshold deve contar (comparação >=)."""
    skill_match = {"matched": [], "partial": [], "missing": ["aws"], "extra": ["cloud"]}
    similarity_fn = _similarity_table({("aws", "cloud"): SEMANTIC_SIMILARITY_THRESHOLD})

    result = enrich_with_semantic_matching(skill_match, score=0, similarity_fn=similarity_fn)

    assert len(result["semantic_matches"]) == 1


def test_best_resume_skill_is_chosen_among_multiple_extras():
    """Quando várias skills extras existem, a de maior similaridade é escolhida."""
    skill_match = {"matched": [], "partial": [], "missing": ["machine learning"], "extra": ["ml", "docker"]}
    similarity_fn = _similarity_table(
        {
            ("machine learning", "ml"): 0.9,
            ("machine learning", "docker"): 0.75,
        }
    )

    result = enrich_with_semantic_matching(skill_match, score=0, similarity_fn=similarity_fn)

    assert result["semantic_matches"][0]["matched_resume_skill"] == "ml"
    assert result["semantic_matches"][0]["similarity"] == 0.9


def test_semantic_matches_limited_to_max_10_items():
    """semantic_matches nunca deve ter mais de MAX_SEMANTIC_MATCHES itens, mesmo com mais gaps cobertos."""
    missing = [f"skill_missing_{i}" for i in range(15)]
    extra = [f"skill_extra_{i}" for i in range(15)]
    skill_match = {"matched": [], "partial": [], "missing": missing, "extra": extra}

    table = {(missing[i], extra[i]): 0.99 for i in range(15)}
    similarity_fn = _similarity_table(table)

    result = enrich_with_semantic_matching(skill_match, score=0, similarity_fn=similarity_fn)

    assert len(result["semantic_matches"]) == MAX_SEMANTIC_MATCHES
    assert MAX_SEMANTIC_MATCHES == 10


def test_semantic_matches_sorted_by_similarity_descending():
    """A lista de semantic_matches deve vir ordenada por similaridade decrescente."""
    skill_match = {
        "matched": [],
        "partial": [],
        "missing": ["skill_a", "skill_b", "skill_c"],
        "extra": ["extra_a", "extra_b", "extra_c"],
    }
    similarity_fn = _similarity_table(
        {
            ("skill_a", "extra_a"): 0.75,
            ("skill_b", "extra_b"): 0.95,
            ("skill_c", "extra_c"): 0.80,
        }
    )

    result = enrich_with_semantic_matching(skill_match, score=0, similarity_fn=similarity_fn)

    similarities = [item["similarity"] for item in result["semantic_matches"]]
    assert similarities == sorted(similarities, reverse=True)


def test_fallback_returns_none_when_similarity_fn_raises_embedding_unavailable():
    """Se o serviço de embeddings falhar, enrich_with_semantic_matching retorna None (fallback)."""

    def _failing_similarity_fn(term_a, term_b):
        raise EmbeddingUnavailableError("simulado")

    skill_match = {"matched": ["python"], "partial": [], "missing": ["aws"], "extra": ["cloud"]}

    result = enrich_with_semantic_matching(skill_match, score=50, similarity_fn=_failing_similarity_fn)

    assert result is None


def test_fallback_returns_none_on_unexpected_exception():
    """Qualquer exceção inesperada do similarity_fn também deve resultar em fallback (None), nunca propagar."""

    def _failing_similarity_fn(term_a, term_b):
        raise ValueError("erro inesperado simulado")

    skill_match = {"matched": ["python"], "partial": [], "missing": ["aws"], "extra": ["cloud"]}

    result = enrich_with_semantic_matching(skill_match, score=50, similarity_fn=_failing_similarity_fn)

    assert result is None


def test_hybrid_score_never_exceeds_100_or_goes_below_0():
    """hybrid_score deve sempre ficar entre 0 e 100, mesmo em cenários extremos."""
    skill_match = {"matched": ["python", "docker"], "partial": [], "missing": [], "extra": []}

    result = enrich_with_semantic_matching(skill_match, score=100, similarity_fn=_similarity_table({}))

    assert 0 <= result["hybrid_score"] <= 100
