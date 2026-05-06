"""
test_matcher.py — Testes unitários do módulo matcher.py.

Testa analyze_skill_match e calculate_weighted_score com:
- Matching simples (matched, missing, extra)
- Matching de idioma com nível (inglês básico/intermediário/avançado)
- Variações em português e inglês
- Score ponderado
"""

from app.matcher import analyze_skill_match, calculate_weighted_score


# ---------------------------------------------------------------------------
# Testes de matching simples
# ---------------------------------------------------------------------------

def test_simple_match_python():
    """Skill presente no currículo e na vaga deve estar em matched."""
    result = analyze_skill_match(["python", "docker"], ["python"])
    assert "python" in result["matched"]
    assert "python" not in result["missing"]


def test_simple_missing_docker():
    """Skill exigida pela vaga mas ausente no currículo deve estar em missing."""
    result = analyze_skill_match(["python"], ["docker"])
    assert "docker" in result["missing"]
    assert "docker" not in result["matched"]


def test_simple_extra_skill():
    """Skill do currículo não exigida pela vaga deve estar em extra."""
    result = analyze_skill_match(["python", "docker"], ["docker"])
    assert "python" in result["extra"]
    assert "python" not in result["matched"]
    assert "python" not in result["missing"]


def test_all_matched():
    """Quando currículo cobre todas as skills da vaga, missing deve ser vazio."""
    result = analyze_skill_match(["python", "docker", "aws"], ["python", "docker", "aws"])
    assert set(result["matched"]) == {"python", "docker", "aws"}
    assert result["missing"] == []
    assert result["partial"] == []


def test_empty_job_skills():
    """Vaga sem skills deve retornar tudo vazio exceto extra."""
    result = analyze_skill_match(["python"], [])
    assert result["matched"] == []
    assert result["partial"] == []
    assert result["missing"] == []
    assert "python" in result["extra"]


def test_empty_resume_skills():
    """Currículo sem skills deve ter todas as skills da vaga em missing."""
    result = analyze_skill_match([], ["python", "docker"])
    assert set(result["missing"]) == {"python", "docker"}
    assert result["matched"] == []
    assert result["extra"] == []


def test_no_duplicates_in_results():
    """Nenhuma skill deve aparecer em mais de uma categoria."""
    result = analyze_skill_match(["python", "docker"], ["python", "aws"])
    all_skills = (
        result["matched"] + result["partial"] +
        result["missing"] + result["extra"]
    )
    assert len(all_skills) == len(set(all_skills))


# ---------------------------------------------------------------------------
# Testes de idioma — nível canônico (gerado por skills.py)
# ---------------------------------------------------------------------------

def test_english_advanced_matched_by_advanced():
    """english_advanced exigido e currículo tem english_advanced → matched."""
    result = analyze_skill_match(["english_advanced"], ["english_advanced"])
    assert "english_advanced" in result["matched"]
    assert result["partial"] == []


def test_english_advanced_partial_by_intermediate():
    """english_advanced exigido e currículo tem english_intermediate → partial."""
    result = analyze_skill_match(["english_intermediate"], ["english_advanced"])
    assert "english_advanced" in result["partial"]
    assert result["matched"] == []


def test_english_advanced_partial_by_basic():
    """english_advanced exigido e currículo tem english_basic → partial."""
    result = analyze_skill_match(["english_basic"], ["english_advanced"])
    assert "english_advanced" in result["partial"]


def test_english_intermediate_matched_by_advanced():
    """english_intermediate exigido e currículo tem english_advanced → matched."""
    result = analyze_skill_match(["english_advanced"], ["english_intermediate"])
    assert "english_intermediate" in result["matched"]
    assert result["partial"] == []


def test_english_intermediate_partial_by_basic():
    """english_intermediate exigido e currículo tem english_basic → partial."""
    result = analyze_skill_match(["english_basic"], ["english_intermediate"])
    assert "english_intermediate" in result["partial"]


def test_english_basic_matched_by_advanced():
    """english_basic exigido e currículo tem english_advanced → matched."""
    result = analyze_skill_match(["english_advanced"], ["english_basic"])
    assert "english_basic" in result["matched"]
    assert result["partial"] == []


def test_english_basic_matched_by_intermediate():
    """english_basic exigido e currículo tem english_intermediate → matched."""
    result = analyze_skill_match(["english_intermediate"], ["english_basic"])
    assert "english_basic" in result["matched"]


def test_english_basic_matched_by_basic():
    """english_basic exigido e currículo tem english_basic → matched."""
    result = analyze_skill_match(["english_basic"], ["english_basic"])
    assert "english_basic" in result["matched"]


# ---------------------------------------------------------------------------
# Testes de idioma — variações em português
# ---------------------------------------------------------------------------

def test_ingles_avancado_matched_by_ingles_avancado():
    """'inglês avançado' exigido e currículo tem 'inglês avançado' → matched."""
    result = analyze_skill_match(["inglês avançado"], ["inglês avançado"])
    assert result["matched"] != []
    assert result["partial"] == []


def test_ingles_avancado_partial_by_ingles_intermediario():
    """'inglês avançado' exigido e currículo tem 'inglês intermediário' → partial."""
    result = analyze_skill_match(["inglês intermediário"], ["inglês avançado"])
    assert result["partial"] != []
    assert result["matched"] == []


def test_ingles_intermediario_matched_by_ingles_avancado():
    """'inglês intermediário' exigido e currículo tem 'inglês avançado' → matched."""
    result = analyze_skill_match(["inglês avançado"], ["inglês intermediário"])
    assert result["matched"] != []
    assert result["partial"] == []


def test_ingles_basico_matched_by_ingles_avancado():
    """'inglês básico' exigido e currículo tem 'inglês avançado' → matched."""
    result = analyze_skill_match(["inglês avançado"], ["inglês básico"])
    assert result["matched"] != []
    assert result["partial"] == []


# ---------------------------------------------------------------------------
# Testes de score ponderado
# ---------------------------------------------------------------------------

def test_weighted_score_all_matched():
    """Score deve ser 100 quando todas as skills estão matched."""
    match_result = {"matched": ["python", "docker"], "partial": [], "missing": []}
    assert calculate_weighted_score(match_result) == 100


def test_weighted_score_all_missing():
    """Score deve ser 0 quando todas as skills estão missing."""
    match_result = {"matched": [], "partial": [], "missing": ["python", "docker"]}
    assert calculate_weighted_score(match_result) == 0


def test_weighted_score_mixed():
    """Score ponderado: 1 matched + 1 partial + 1 missing = (1.5/3)*100 = 50."""
    match_result = {
        "matched": ["python"],
        "partial": ["english_advanced"],
        "missing": ["docker"],
    }
    assert calculate_weighted_score(match_result) == 50


def test_weighted_score_only_partial():
    """Score com apenas partial: (0.5/1)*100 = 50."""
    match_result = {"matched": [], "partial": ["english_advanced"], "missing": []}
    assert calculate_weighted_score(match_result) == 50


def test_weighted_score_empty_job():
    """Score deve ser 0 quando não há skills exigidas."""
    match_result = {"matched": [], "partial": [], "missing": []}
    assert calculate_weighted_score(match_result) == 0


def test_weighted_score_two_matched_one_partial():
    """2 matched + 1 partial = (2.5/3)*100 = 83."""
    match_result = {
        "matched": ["python", "docker"],
        "partial": ["english_advanced"],
        "missing": [],
    }
    assert calculate_weighted_score(match_result) == 83
