"""
recommender.py — Geração de recomendações de melhoria do currículo.

Gera recomendações específicas e acionáveis baseadas nas skills faltantes,
skills parciais e no score de compatibilidade.

Ponto de extensão para LLM (melhoria futura):
    Esta função pode ser substituída por uma versão que chama um LLM
    (OpenAI, Anthropic, Ollama) para gerar recomendações mais naturais
    e personalizadas. A interface de generate_recommendations permanece a mesma.
"""

# Limite máximo de recomendações por análise
MAX_RECOMMENDATIONS = 10

# Limite de skills faltantes listadas individualmente
MAX_SKILL_RECOMMENDATIONS = 8

# Skills de idioma canônicas (geradas por skills.py)
_LANGUAGE_SKILLS = {
    "english_basic", "english_intermediate", "english_advanced",
    "espanhol", "frances", "alemao", "mandarin", "japones",
}

# Skills de cloud e DevOps — recebem sugestão de projeto de deploy/automação
_CLOUD_DEVOPS_SKILLS = {
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "circleci", "ci/cd",
    "heroku", "vercel", "netlify", "cloudflare",
}

# Mapeamento de nome canônico de idioma para nome legível
_LANGUAGE_DISPLAY = {
    "english_basic":        "Inglês (básico)",
    "english_intermediate": "Inglês (intermediário)",
    "english_advanced":     "Inglês (avançado)",
    "espanhol":             "Espanhol",
    "frances":              "Francês",
    "alemao":               "Alemão",
    "mandarin":             "Mandarim",
    "japones":              "Japonês",
}


def _recommendation_for_missing_skill(skill: str) -> str:
    """Gera recomendação específica para uma skill faltante."""
    if skill in _LANGUAGE_SKILLS:
        display = _LANGUAGE_DISPLAY.get(skill, skill.capitalize())
        return (
            f"A vaga exige {display}. Informe seu nível CEFR (ex: B2, C1) no currículo "
            f"e comprove com certificação (TOEFL, IELTS, DELE) ou experiência profissional documentada."
        )
    if skill in _CLOUD_DEVOPS_SKILLS:
        return (
            f"A vaga exige {skill}. Crie um projeto de deploy ou automação usando {skill} "
            f"e publique no GitHub com documentação clara."
        )
    return (
        f"A vaga exige {skill}. Desenvolva um projeto prático que demonstre essa skill "
        f"e adicione ao seu portfólio ou currículo com descrição dos resultados."
    )


def _recommendation_for_partial_skill(skill: str) -> str:
    """Gera recomendação específica para uma skill parcialmente atendida."""
    if skill in _LANGUAGE_SKILLS or "english" in skill:
        return (
            "Seu nível de inglês está abaixo do exigido pela vaga. "
            "Informe seu nível CEFR atual no currículo (ex: B2) e considere "
            "obter uma certificação reconhecida (TOEFL, IELTS) para aumentar sua credibilidade."
        )
    return (
        f"Sua experiência com {skill} pode não atender completamente o exigido. "
        f"Destaque projetos concretos e resultados mensuráveis para demonstrar proficiência."
    )


def generate_recommendations(
    missing_skills: list[str],
    score: int,
    partial_skills: list[str] | None = None,
) -> list[str]:
    """
    Gera uma lista de recomendações textuais específicas e acionáveis.

    Lógica:
        1. Se não há skills faltantes nem parciais: retorna mensagem de parabéns.
        2. Para cada skill faltante (até 6): recomendação específica por categoria.
        3. Para skills parciais (até 2): recomendação de melhoria de nível.
        4. Mensagem contextual baseada no score (baixo/médio/alto).
        5. Total nunca excede 10 recomendações.

    Args:
        missing_skills: Skills da vaga ausentes no currículo.
        score: Score de compatibilidade entre 0 e 100.
        partial_skills: Skills parcialmente atendidas (ex: idioma em nível inferior).

    Returns:
        Lista de strings com recomendações. Máximo de 10 itens.
    """
    missing_skills = [s for s in (missing_skills or []) if s]
    partial_skills = [s for s in (partial_skills or []) if s]

    recommendations: list[str] = []

    # Caso especial: sem gaps
    if not missing_skills and not partial_skills:
        recommendations.append(
            "Seu currículo já cobre todas as skills identificadas na vaga. Parabéns!"
        )
        return recommendations

    # Recomendações para skills faltantes (até 6 para deixar espaço para parciais e score)
    max_missing = min(6, MAX_SKILL_RECOMMENDATIONS)
    for skill in missing_skills[:max_missing]:
        recommendations.append(_recommendation_for_missing_skill(skill))

    # Recomendações para skills parciais (até 2)
    for skill in partial_skills[:2]:
        rec = _recommendation_for_partial_skill(skill)
        if rec not in recommendations:
            recommendations.append(rec)

    # Mensagem contextual baseada no score
    if score < 40:
        recommendations.append(
            "Seu perfil tem baixa compatibilidade com esta vaga. "
            "Priorize os requisitos essenciais acima antes de se candidatar — "
            "construa evidências práticas (projetos, certificações) para cada skill crítica."
        )
    elif score < 80:
        recommendations.append(
            "Seu perfil tem compatibilidade moderada com esta vaga. "
            "Reposicione suas experiências mais relevantes para o topo do currículo "
            "e quantifique resultados sempre que possível."
        )
    else:
        recommendations.append(
            "Seu perfil tem alta compatibilidade com esta vaga. "
            "Destaque as skills em comum no início do currículo, "
            "quantifique seus resultados e personalize o resumo profissional para esta vaga."
        )

    return recommendations[:MAX_RECOMMENDATIONS]
