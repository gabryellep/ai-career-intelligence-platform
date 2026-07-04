"""
test_recommender.py — Testes unitários do módulo recommender.py.

Testa a função generate_recommendations com os seguintes cenários:
1. Sem skills faltantes → retorna apenas mensagem de parabéns
2. Score < 40 → inclui mensagem de baixa compatibilidade
3. Score >= 80 → inclui mensagem positiva
4. Número máximo de recomendações <= 10
5. Uma recomendação por skill faltante (até 8)
"""

from app.engines.deterministic.recommender import generate_recommendations

# ---------------------------------------------------------------------------
# Mensagens esperadas (constantes para evitar typos nos testes)
# ---------------------------------------------------------------------------

MSG_PARABENS = "Seu currículo já cobre todas as skills identificadas na vaga. Parabéns!"
MSG_BAIXA = (
    "Seu perfil tem baixa compatibilidade com esta vaga. "
    "Priorize os requisitos essenciais acima antes de se candidatar — "
    "construa evidências práticas (projetos, certificações) para cada skill crítica."
)
MSG_MEDIA = (
    "Seu perfil tem compatibilidade moderada com esta vaga. "
    "Reposicione suas experiências mais relevantes para o topo do currículo "
    "e quantifique resultados sempre que possível."
)
MSG_ALTA = (
    "Seu perfil tem alta compatibilidade com esta vaga. "
    "Destaque as skills em comum no início do currículo, "
    "quantifique seus resultados e personalize o resumo profissional para esta vaga."
)


# ---------------------------------------------------------------------------
# Testes: sem skills faltantes
# ---------------------------------------------------------------------------


def test_no_missing_skills_returns_congratulations():
    """Sem skills faltantes deve retornar apenas a mensagem de parabéns."""
    result = generate_recommendations([], 70)

    assert len(result) == 1
    assert result[0] == MSG_PARABENS


def test_no_missing_skills_score_low_returns_only_congratulations():
    """Sem skills faltantes, mesmo com score baixo, retorna apenas parabéns."""
    result = generate_recommendations([], 20)

    assert len(result) == 1
    assert result[0] == MSG_PARABENS


def test_no_missing_skills_score_high_returns_only_congratulations():
    """Sem skills faltantes, mesmo com score alto, retorna apenas parabéns."""
    result = generate_recommendations([], 95)

    assert len(result) == 1
    assert result[0] == MSG_PARABENS


# ---------------------------------------------------------------------------
# Testes: score < 40
# ---------------------------------------------------------------------------


def test_low_score_includes_warning_message():
    """Score < 40 deve incluir mensagem de baixa compatibilidade."""
    result = generate_recommendations(["docker", "aws"], 30)

    assert MSG_BAIXA in result


def test_low_score_boundary_39():
    """Score 39 (limite inferior) deve incluir mensagem de baixa compatibilidade."""
    result = generate_recommendations(["docker"], 39)

    assert MSG_BAIXA in result


def test_score_40_does_not_include_low_warning():
    """Score 40 (fora do limite) não deve incluir mensagem de baixa compatibilidade."""
    result = generate_recommendations(["docker"], 40)

    assert MSG_BAIXA not in result


# ---------------------------------------------------------------------------
# Testes: score >= 80
# ---------------------------------------------------------------------------


def test_high_score_includes_positive_message():
    """Score >= 80 deve incluir mensagem positiva."""
    result = generate_recommendations(["docker"], 85)

    assert MSG_ALTA in result


def test_high_score_boundary_80():
    """Score 80 (limite exato) deve incluir mensagem positiva."""
    result = generate_recommendations(["docker"], 80)

    assert MSG_ALTA in result


def test_score_79_does_not_include_high_message():
    """Score 79 (abaixo do limite) não deve incluir mensagem positiva."""
    result = generate_recommendations(["docker"], 79)

    assert MSG_ALTA not in result


# ---------------------------------------------------------------------------
# Testes: limite máximo de recomendações
# ---------------------------------------------------------------------------


def test_max_recommendations_never_exceeds_10():
    """O retorno nunca deve exceder 10 recomendações."""
    many_skills = [f"skill_{i}" for i in range(20)]
    result = generate_recommendations(many_skills, 10)

    assert len(result) <= 10


def test_max_recommendations_with_high_score():
    """Mesmo com score alto e muitas skills, o limite de 10 deve ser respeitado."""
    many_skills = [f"skill_{i}" for i in range(20)]
    result = generate_recommendations(many_skills, 85)

    assert len(result) <= 10


def test_return_type_is_list():
    """O retorno deve ser sempre uma lista."""
    result = generate_recommendations(["docker"], 50)
    assert isinstance(result, list)


def test_all_items_are_strings():
    """Todos os itens da lista devem ser strings."""
    result = generate_recommendations(["docker", "aws"], 50)
    for item in result:
        assert isinstance(item, str)


# ---------------------------------------------------------------------------
# Testes: uma recomendação por skill faltante (até 8)
# ---------------------------------------------------------------------------


def test_one_recommendation_per_missing_skill():
    """Deve gerar uma recomendação para cada skill faltante."""
    missing = ["docker", "aws", "kubernetes"]
    result = generate_recommendations(missing, 50)

    for skill in missing:
        # Verifica que existe pelo menos uma recomendação mencionando a skill
        assert any(skill in rec for rec in result), f"Nenhuma recomendação menciona '{skill}'"


def test_max_8_skill_recommendations():
    """Deve gerar no máximo 6 recomendações individuais de skills (novo limite)."""
    missing = [f"skill_{i}" for i in range(10)]
    result = generate_recommendations(missing, 50)

    # Recomendações de skill são as que mencionam "skill_" no texto
    skill_recs = [r for r in result if "skill_" in r]
    assert len(skill_recs) <= 6


def test_skills_beyond_limit_are_not_included():
    """Skills além do limite não devem gerar recomendações individuais."""
    missing = [f"skill_{i}" for i in range(10)]
    result = generate_recommendations(missing, 50)

    # skill_6 a skill_9 não devem aparecer (limite é 6)
    for i in range(6, 10):
        assert not any(f"skill_{i}" in r for r in result), f"skill_{i} não deveria aparecer"


# ---------------------------------------------------------------------------
# Testes de ordem e conteúdo exato
# ---------------------------------------------------------------------------


def test_exact_output_low_score():
    """Valida que o resultado com score < 40 contém recomendações de skill e mensagem de baixa compatibilidade."""
    missing = ["docker", "aws"]
    result = generate_recommendations(missing, 30)

    # Verifica que cada skill está mencionada
    assert any("docker" in r for r in result)
    assert any("aws" in r for r in result)
    # Verifica que a mensagem de baixa compatibilidade está presente e é a última
    assert result[-1] == MSG_BAIXA


def test_high_score_message_is_last():
    """Quando score >= 80, a mensagem positiva deve ser sempre o último item."""
    result = generate_recommendations(["docker", "aws"], 85)

    assert len(result) > 0
    assert result[-1] == MSG_ALTA


def test_low_score_message_is_last():
    """Quando score < 40, a mensagem de baixa compatibilidade deve ser sempre o último item."""
    result = generate_recommendations(["docker", "aws"], 30)

    assert len(result) > 0
    assert result[-1] == MSG_BAIXA
