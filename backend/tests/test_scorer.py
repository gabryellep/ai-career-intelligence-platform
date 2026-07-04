"""
test_scorer.py — Testes unitários do módulo scorer.py.

Testa a função calculate_score com os seguintes cenários:
1. Score 100% — currículo contém todas as skills da vaga
2. Score 0% — nenhuma skill em comum
3. Score parcial — currículo contém parte das skills da vaga
4. Vaga vazia — retorna (0, [], [])
5. Score sempre entre 0 e 100
6. Consistência: matched ∪ missing == job_skills
7. Tipos de retorno corretos
"""

from app.engines.deterministic.scorer import calculate_score

# ---------------------------------------------------------------------------
# Testes de score
# ---------------------------------------------------------------------------


def test_score_100_percent():
    """Currículo com todas as skills da vaga deve retornar score 100."""
    resume = ["python", "docker", "aws"]
    job = ["python", "docker", "aws"]

    score, matched, missing = calculate_score(resume, job)

    assert score == 100
    assert set(matched) == {"python", "docker", "aws"}
    assert missing == []


def test_score_0_percent():
    """Currículo sem nenhuma skill da vaga deve retornar score 0."""
    resume = ["java", "spring boot"]
    job = ["python", "docker", "aws"]

    score, matched, missing = calculate_score(resume, job)

    assert score == 0
    assert matched == []
    assert set(missing) == {"python", "docker", "aws"}


def test_score_partial():
    """Currículo com parte das skills da vaga deve retornar score proporcional."""
    resume = ["python", "docker"]
    job = ["python", "docker", "aws"]

    score, matched, missing = calculate_score(resume, job)

    # 2 de 3 skills = round(2/3 * 100) = 67
    assert score == 67
    assert set(matched) == {"python", "docker"}
    assert missing == ["aws"]


def test_score_with_empty_job_skills():
    """Vaga sem skills deve retornar (0, [], [])."""
    score, matched, missing = calculate_score(["python", "docker"], [])

    assert score == 0
    assert matched == []
    assert missing == []


def test_score_with_empty_resume_skills():
    """Currículo sem skills deve retornar score 0 com todas as skills da vaga como missing."""
    resume = []
    job = ["python", "docker", "aws"]

    score, matched, missing = calculate_score(resume, job)

    assert score == 0
    assert matched == []
    assert set(missing) == {"python", "docker", "aws"}


def test_score_with_both_empty():
    """Ambas as listas vazias devem retornar (0, [], [])."""
    score, matched, missing = calculate_score([], [])

    assert score == 0
    assert matched == []
    assert missing == []


# ---------------------------------------------------------------------------
# Testes de invariantes
# ---------------------------------------------------------------------------


def test_score_is_between_0_and_100():
    """O score deve sempre estar entre 0 e 100, inclusive."""
    casos = [
        (["python"], ["python"]),
        ([], ["python", "docker"]),
        (["python", "docker", "aws"], ["python"]),
        (["python"], []),
        ([], []),
    ]
    for resume, job in casos:
        score, _, _ = calculate_score(resume, job)
        assert 0 <= score <= 100, f"Score fora do intervalo: {score} para resume={resume}, job={job}"


def test_matched_union_missing_equals_job_skills():
    """A união de matched e missing deve ser igual ao conjunto de job_skills."""
    resume = ["python", "docker"]
    job = ["python", "docker", "aws", "kubernetes"]

    score, matched, missing = calculate_score(resume, job)

    assert set(matched) | set(missing) == set(job)


def test_matched_and_missing_are_disjoint():
    """matched e missing não devem ter elementos em comum."""
    resume = ["python", "docker"]
    job = ["python", "docker", "aws"]

    score, matched, missing = calculate_score(resume, job)

    assert set(matched) & set(missing) == set()


# ---------------------------------------------------------------------------
# Testes de tipos de retorno
# ---------------------------------------------------------------------------


def test_return_types():
    """O retorno deve ser uma tupla (int, list, list)."""
    result = calculate_score(["python"], ["python", "docker"])
    score, matched, missing = result

    assert isinstance(score, int)
    assert isinstance(matched, list)
    assert isinstance(missing, list)


def test_matched_and_missing_are_sorted():
    """matched e missing devem ser listas ordenadas."""
    resume = ["python", "docker", "aws"]
    job = ["python", "docker", "aws", "kubernetes", "terraform"]

    score, matched, missing = calculate_score(resume, job)

    assert matched == sorted(matched)
    assert missing == sorted(missing)


# ---------------------------------------------------------------------------
# Testes de casos com skills extras no currículo
# ---------------------------------------------------------------------------


def test_extra_resume_skills_do_not_affect_score():
    """Skills extras no currículo que não estão na vaga não devem afetar o score."""
    resume = ["python", "docker", "java", "ruby", "perl"]  # java, ruby, perl são extras
    job = ["python", "docker"]

    score, matched, missing = calculate_score(resume, job)

    assert score == 100
    assert set(matched) == {"python", "docker"}
    assert missing == []


# ---------------------------------------------------------------------------
# Testes complementares
# ---------------------------------------------------------------------------


def test_duplicate_resume_skills_do_not_affect_score():
    """Duplicatas em resume_skills não devem afetar o score nem os resultados."""
    resume_with_duplicates = ["python", "python", "docker", "docker", "docker"]
    resume_clean = ["python", "docker"]
    job = ["python", "docker", "aws"]

    score_dup, matched_dup, missing_dup = calculate_score(resume_with_duplicates, job)
    score_clean, matched_clean, missing_clean = calculate_score(resume_clean, job)

    assert score_dup == score_clean
    assert set(matched_dup) == set(matched_clean)
    assert set(missing_dup) == set(missing_clean)


def test_duplicate_job_skills_do_not_affect_score():
    """Duplicatas em job_skills não devem afetar o score nem os resultados."""
    resume = ["python", "docker"]
    job_with_duplicates = ["python", "python", "docker", "aws", "aws"]
    job_clean = ["python", "docker", "aws"]

    score_dup, matched_dup, missing_dup = calculate_score(resume, job_with_duplicates)
    score_clean, matched_clean, missing_clean = calculate_score(resume, job_clean)

    assert score_dup == score_clean
    assert set(matched_dup) == set(matched_clean)
    assert set(missing_dup) == set(missing_clean)


def test_score_is_case_sensitive_by_design():
    """
    O scorer opera sobre listas já normalizadas pelo extract_skills.
    Por design, calculate_score é case-sensitive — a normalização
    para minúsculas é responsabilidade do Skills_Extractor.
    Skills em maiúsculas passadas diretamente não fazem match com minúsculas.
    """
    resume_upper = ["PYTHON", "DOCKER"]
    job_lower = ["python", "docker"]

    score, matched, missing = calculate_score(resume_upper, job_lower)

    # Sem normalização, "PYTHON" != "python" — score deve ser 0
    assert score == 0
    assert matched == []
    assert set(missing) == {"python", "docker"}
