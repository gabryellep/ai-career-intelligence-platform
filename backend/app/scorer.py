"""
scorer.py — Cálculo do score de compatibilidade entre currículo e vaga.

Fórmula:
    score = round( |skills_currículo ∩ skills_vaga| / |skills_vaga| × 100 )

Limitação documentada:
    O score considera apenas a presença de skills e não leva em conta
    nível de experiência, contexto ou relevância semântica.
"""


def calculate_score(
    resume_skills: list[str],
    job_skills: list[str],
) -> tuple[int, list[str], list[str]]:
    """
    Calcula o score de compatibilidade entre as skills do currículo e da vaga.

    Args:
        resume_skills: Lista de skills extraídas do currículo.
        job_skills: Lista de skills extraídas da descrição da vaga.

    Returns:
        Tupla com três elementos:
            - score (int): Valor entre 0 e 100 representando a compatibilidade.
            - matched_skills (list[str]): Skills presentes no currículo e na vaga.
            - missing_skills (list[str]): Skills da vaga ausentes no currículo.

    Exemplos:
        >>> calculate_score(["python", "docker"], ["python", "docker", "aws"])
        (67, ['docker', 'python'], ['aws'])

        >>> calculate_score([], ["python"])
        (0, [], ['python'])

        >>> calculate_score(["python"], [])
        (0, [], [])
    """
    # Se a vaga não tem skills identificadas, score é 0
    if not job_skills:
        return (0, [], [])

    # Converte para sets para operações de conjunto eficientes
    resume_set = set(resume_skills)
    job_set = set(job_skills)

    # Skills presentes em ambos (interseção)
    matched_set = resume_set & job_set

    # Skills da vaga que não estão no currículo (diferença)
    missing_set = job_set - resume_set

    # Calcula o score: proporção de skills da vaga cobertas pelo currículo
    score = round(len(matched_set) / len(job_set) * 100)

    # Garante que o score está no intervalo [0, 100]
    score = max(0, min(100, score))

    # Retorna listas ordenadas para resultado consistente
    return (
        score,
        sorted(matched_set),
        sorted(missing_set),
    )
