"""
matcher.py — Motor de matching inteligente entre skills do currículo e da vaga.

Diferente do scorer.py (que faz matching binário), o matcher suporta:
- Matching parcial para idiomas com nível (ex: intermediate atende parcialmente advanced)
- Normalização de variações em português e inglês
- Campo "extra" com skills do currículo além do exigido

Este módulo é independente — não substitui scorer.py ainda.
Pode ser integrado ao analyzer.py em uma versão futura.
"""

# ---------------------------------------------------------------------------
# Mapeamento de nível de inglês
# Aceita variações em português e inglês
# ---------------------------------------------------------------------------

# Nível numérico: quanto maior, mais avançado
_ENGLISH_LEVEL: dict[str, int] = {
    # Canônicos (gerados por skills.py)
    "english_basic": 1,
    "english_intermediate": 2,
    "english_advanced": 3,
    # Variações em português
    "inglês básico": 1,
    "ingles basico": 1,
    "inglês intermediário": 2,
    "ingles intermediario": 2,
    "inglês avançado": 3,
    "ingles avancado": 3,
    # Variações em inglês
    "basic english": 1,
    "intermediate english": 2,
    "advanced english": 3,
    "fluent english": 3,
    "fluente em inglês": 3,
    "fluente em ingles": 3,
    # Níveis CEFR
    "a1": 1,
    "a2": 1,
    "b1": 2,
    "b2": 2,
    "c1": 3,
    "c2": 3,
}

# Conjunto de todas as chaves que representam inglês (qualquer nível)
_ENGLISH_KEYS = frozenset(_ENGLISH_LEVEL.keys())


def _get_english_level(skill: str) -> int | None:
    """
    Retorna o nível numérico de inglês para uma skill, ou None se não for inglês.
    """
    return _ENGLISH_LEVEL.get(skill.lower().strip())


def _is_english_skill(skill: str) -> bool:
    """Retorna True se a skill representa algum nível de inglês."""
    return _get_english_level(skill) is not None


# ---------------------------------------------------------------------------
# Matching principal
# ---------------------------------------------------------------------------


def analyze_skill_match(
    resume_skills: list[str],
    job_skills: list[str],
) -> dict:
    """
    Analisa o matching entre as skills do currículo e as skills exigidas pela vaga.

    Suporta matching parcial para idiomas com nível:
        - Currículo atende ou supera o nível exigido → matched
        - Currículo tem nível inferior ao exigido → partial
        - Currículo não tem o idioma → missing

    Para skills normais:
        - Skill da vaga presente no currículo → matched
        - Skill da vaga ausente no currículo → missing

    Args:
        resume_skills: Lista de skills extraídas do currículo.
        job_skills: Lista de skills exigidas pela vaga.

    Returns:
        Dicionário com:
            - matched (list[str]): Skills da vaga completamente atendidas.
            - partial (list[str]): Skills da vaga parcialmente atendidas.
            - missing (list[str]): Skills da vaga ausentes no currículo.
            - extra (list[str]): Skills do currículo além do exigido pela vaga.
    """
    resume_set = set(s.lower().strip() for s in (resume_skills or []))
    job_set = set(s.lower().strip() for s in (job_skills or []))

    matched: list[str] = []
    partial: list[str] = []
    missing: list[str] = []

    # Skills do currículo já "usadas" (matched ou partial) — não entram em extra
    used_resume_skills: set[str] = set()

    for job_skill in sorted(job_set):
        job_level = _get_english_level(job_skill)

        if job_level is not None:
            # Skill de idioma — busca o melhor nível disponível no currículo
            best_resume_level = max(
                (_get_english_level(s) for s in resume_set if _get_english_level(s) is not None),
                default=None,
            )

            if best_resume_level is None:
                # Currículo não tem nenhum nível de inglês
                missing.append(job_skill)
            elif best_resume_level >= job_level:
                # Currículo atende ou supera o nível exigido
                matched.append(job_skill)
                # Marca todas as skills de inglês do currículo como usadas
                for s in resume_set:
                    if _get_english_level(s) is not None:
                        used_resume_skills.add(s)
            else:
                # Currículo tem inglês, mas nível inferior ao exigido
                partial.append(job_skill)
                for s in resume_set:
                    if _get_english_level(s) is not None:
                        used_resume_skills.add(s)
        else:
            # Skill normal — matching exato
            if job_skill in resume_set:
                matched.append(job_skill)
                used_resume_skills.add(job_skill)
            else:
                missing.append(job_skill)

    # Extra: skills do currículo não usadas no matching
    extra = sorted(resume_set - used_resume_skills)

    return {
        "matched": sorted(matched),
        "partial": sorted(partial),
        "missing": sorted(missing),
        "extra": extra,
    }


def calculate_weighted_score(match_result: dict) -> int:
    """
    Calcula o score ponderado com base no resultado do matching.

    Pesos:
        - matched: 1.0 ponto
        - partial: 0.5 ponto
        - missing: 0.0 ponto

    Fórmula:
        score = round((pontos / total_exigido) * 100)
        onde total_exigido = len(matched) + len(partial) + len(missing)

    Args:
        match_result: Dicionário retornado por analyze_skill_match().

    Returns:
        Score inteiro entre 0 e 100.
        Retorna 0 se não houver skills exigidas pela vaga.
    """
    matched = match_result.get("matched", [])
    partial = match_result.get("partial", [])
    missing = match_result.get("missing", [])

    total_required = len(matched) + len(partial) + len(missing)

    if total_required == 0:
        return 0

    points = len(matched) * 1.0 + len(partial) * 0.5
    return round((points / total_required) * 100)
