"""
scripts/semantic_demo.py — Validação manual do matching semântico real (SPEC 0012).

Ferramenta de exploração/documentação — NÃO faz parte do produto: não é
importada por nenhum módulo de app/ nem por main.py, não roda no CI, não é
coberta por pytest (ver SPEC 0012, seção 6 — decisão deliberada, não lacuna
de cobertura). Requer sentence-transformers instalado
(`pip install -r requirements-dev.txt`) — na primeira execução, baixa os
pesos do modelo (~90 MB) do Hugging Face Hub para o cache local.

Uso (a partir de backend/):
    python scripts/semantic_demo.py

Nunca usa PDF, texto de currículo ou de vaga reais — apenas nomes
sintéticos de skills, escritos diretamente neste arquivo. Não persiste nada
no banco (não importa app.db nem app.repositories) e não liga
ENABLE_SEMANTIC_MATCHING em nenhum lugar — chama as funções do motor
semântico diretamente, independentemente da flag.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engines.deterministic.matcher import analyze_skill_match, calculate_weighted_score  # noqa: E402
from app.engines.semantic.embedding_service import EmbeddingUnavailableError, compute_similarity  # noqa: E402
from app.engines.semantic.hybrid import SEMANTIC_SIMILARITY_THRESHOLD, enrich_with_semantic_matching  # noqa: E402

OUTPUT_MD_PATH = Path(__file__).resolve().parent / "semantic_demo_output.md"

# Pares de aproximação semântica esperada (SPEC 0012, seção 4.2) — skill da
# vaga não cadastrada como alias exato no motor determinístico, mas
# semanticamente relacionada a uma skill do currículo.
EXPECTED_MATCHES = [
    ("docker", "containers"),
    ("postgresql", "relational database"),
    ("fastapi", "python api"),
    ("nlp", "text processing"),
    ("react", "frontend"),
    ("ci/cd", "github actions"),
]

# Pares de falso positivo esperado — skills sem relação técnica real. O
# script evidencia o resultado real, sem mascarar se o modelo aproximar
# algum destes pares indevidamente (ver SPEC 0012, seção 4.6).
EXPECTED_FALSE_POSITIVES = [
    ("react", "postgresql"),
    ("docker", "ux design"),
    ("python", "excel"),
]

# Cenário de antes/depois (SPEC 0012, seção 4.4) — skills sintéticas de uma
# vaga e de um currículo fictícios, nunca texto real.
SCENARIO_JOB_SKILLS = ["python", "docker", "postgresql", "ci/cd", "aws"]
SCENARIO_RESUME_SKILLS = ["python", "containers", "relational database", "github actions"]


def _classify(job_skill: str, resume_skill: str, similarity: float, expected_match: bool) -> dict:
    """Gera a nota interpretável para um par (SPEC 0012, seção 4.3)."""
    above_threshold = similarity >= SEMANTIC_SIMILARITY_THRESHOLD

    if expected_match and above_threshold:
        note = f"Aproximação esperada confirmada — acima do threshold ({SEMANTIC_SIMILARITY_THRESHOLD})."
    elif expected_match and not above_threshold:
        note = (
            f"Aproximação esperada NÃO confirmada — similaridade abaixo do threshold "
            f"({SEMANTIC_SIMILARITY_THRESHOLD}). Limitação real do modelo para este par."
        )
    elif not expected_match and above_threshold:
        note = (
            f"Falso positivo confirmado — modelo aproximou termos sem relação técnica real, "
            f"acima do threshold ({SEMANTIC_SIMILARITY_THRESHOLD})."
        )
    else:
        note = f"Falso positivo evitado — corretamente abaixo do threshold ({SEMANTIC_SIMILARITY_THRESHOLD})."

    return {
        "job_skill": job_skill,
        "resume_skill": resume_skill,
        "similarity": round(similarity, 2),
        "above_threshold": above_threshold,
        "note": note,
    }


def run_pair_comparisons() -> list[dict]:
    """Roda compute_similarity (modelo real) sobre todos os pares de teste."""
    results = []
    for job_skill, resume_skill in EXPECTED_MATCHES:
        similarity = compute_similarity(job_skill, resume_skill)
        results.append(_classify(job_skill, resume_skill, similarity, expected_match=True))
    for job_skill, resume_skill in EXPECTED_FALSE_POSITIVES:
        similarity = compute_similarity(job_skill, resume_skill)
        results.append(_classify(job_skill, resume_skill, similarity, expected_match=False))
    return results


def run_before_after_scenario() -> dict:
    """
    Roda o cenário completo (SPEC 0012, seção 4.4): motor determinístico
    (analyze_skill_match/calculate_weighted_score) seguido do enriquecimento
    semântico real (enrich_with_semantic_matching, sem mock), usando as
    mesmas funções de produção da SPEC 0011.
    """
    skill_match = analyze_skill_match(SCENARIO_RESUME_SKILLS, SCENARIO_JOB_SKILLS)
    deterministic_score = calculate_weighted_score(skill_match)

    semantic_result = enrich_with_semantic_matching(skill_match, deterministic_score)

    return {
        "resume_skills": SCENARIO_RESUME_SKILLS,
        "job_skills": SCENARIO_JOB_SKILLS,
        "match_details": skill_match,
        "score": deterministic_score,
        "semantic_score": semantic_result["semantic_score"] if semantic_result else None,
        "hybrid_score": semantic_result["hybrid_score"] if semantic_result else None,
        "semantic_matches": semantic_result["semantic_matches"] if semantic_result else [],
    }


def render_markdown(pair_results: list[dict], scenario: dict) -> str:
    lines = [
        "# Validação semântica real — SPEC 0012",
        "",
        f"Modelo: `all-MiniLM-L6-v2` (sentence-transformers). Threshold: `{SEMANTIC_SIMILARITY_THRESHOLD}`.",
        "",
        "Gerado localmente por `backend/scripts/semantic_demo.py` — não faz parte do CI nem do deploy.",
        "",
        "## Pares de skills",
        "",
        "| Skill da vaga | Skill do currículo | Similaridade | Acima do threshold | Observação |",
        "|---|---|---|---|---|",
    ]
    for item in pair_results:
        lines.append(
            f"| {item['job_skill']} | {item['resume_skill']} | {item['similarity']} | "
            f"{'sim' if item['above_threshold'] else 'não'} | {item['note']} |"
        )

    lines += [
        "",
        "## Cenário antes/depois",
        "",
        f"- Skills do currículo (sintéticas): {', '.join(scenario['resume_skills'])}",
        f"- Skills da vaga (sintéticas): {', '.join(scenario['job_skills'])}",
        f"- `score` (determinístico): {scenario['score']}",
        f"- `semantic_score`: {scenario['semantic_score']}",
        f"- `hybrid_score`: {scenario['hybrid_score']}",
        "- `semantic_matches`:",
    ]
    if scenario["semantic_matches"]:
        for match in scenario["semantic_matches"]:
            lines.append(
                f"  - `{match['job_skill']}` ≈ `{match['matched_resume_skill']}` "
                f"(similaridade {match['similarity']})"
            )
    else:
        lines.append("  - (nenhum)")

    return "\n".join(lines) + "\n"


def main() -> None:
    try:
        pair_results = run_pair_comparisons()
        scenario = run_before_after_scenario()
    except EmbeddingUnavailableError as exc:
        print(
            "Erro: o modelo de embeddings não pôde ser carregado ou usado. "
            "Instale as dependências com `pip install -r requirements-dev.txt` "
            "e verifique sua conexão de rede (o modelo é baixado do Hugging Face "
            "Hub na primeira execução).",
            file=sys.stderr,
        )
        print(f"Detalhe: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(pair_results, ensure_ascii=False, indent=2))

    markdown = render_markdown(pair_results, scenario)
    OUTPUT_MD_PATH.write_text(markdown, encoding="utf-8")
    print(f"\nRelatório Markdown gerado em: {OUTPUT_MD_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
