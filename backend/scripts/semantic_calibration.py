"""
scripts/semantic_calibration.py — Calibração do matching semântico (SPEC 0013).

Ferramenta de exploração/documentação — NÃO faz parte do produto: não é
importada por nenhum módulo de app/ nem por main.py, não roda no CI, não é
coberta por pytest (mesma decisão e justificativa da SPEC 0012, seção 6).
Requer sentence-transformers instalado (`pip install -r requirements-dev.txt`).

Diferença em relação a scripts/semantic_demo.py (SPEC 0012): aquele é uma
demonstração qualitativa com poucos pares, pensada para README/LinkedIn;
este é quantitativo — roda uma amostra ampliada de pares positivos/negativos
contra vários thresholds candidatos e mede precision/recall/F1 de cada um,
para decidir se SEMANTIC_SIMILARITY_THRESHOLD (app/engines/semantic/hybrid.py)
deve mudar.

Uso (a partir de backend/):
    python scripts/semantic_calibration.py

Nunca usa PDF, texto de currículo ou de vaga reais — apenas nomes
sintéticos de skills. Não persiste nada no banco (não importa app.db nem
app.repositories) e não liga ENABLE_SEMANTIC_MATCHING em nenhum lugar —
chama compute_similarity diretamente, independentemente da flag.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engines.semantic.embedding_service import EmbeddingUnavailableError, compute_similarity  # noqa: E402
from app.engines.semantic.hybrid import SEMANTIC_SIMILARITY_THRESHOLD  # noqa: E402

OUTPUT_MD_PATH = Path(__file__).resolve().parent / "semantic_calibration_output.md"

# Thresholds candidatos a avaliar (SPEC 0013, decisão aprovada) — o
# threshold de produção atual é sempre incluído para comparação direta.
CANDIDATE_THRESHOLDS = [0.50, 0.55, 0.60, 0.65, 0.70]

# ---------------------------------------------------------------------------
# Amostra de calibração (SPEC 0013, seção 4.1) — apenas nomes sintéticos de
# skills, nunca texto de currículo ou vaga reais.
# ---------------------------------------------------------------------------

# Pares que um humano razoável consideraria equivalentes/fortemente
# relacionados, mesmo com redação diferente (rótulo esperado: positivo).
POSITIVE_PAIRS: list[tuple[str, str]] = [
    ("docker", "containers"),
    ("postgresql", "relational database"),
    ("fastapi", "python api"),
    ("nlp", "text processing"),
    ("react", "frontend"),
    ("ci/cd", "github actions"),
    ("machine learning", "ml"),
    ("kubernetes", "container orchestration"),
    ("aws", "cloud computing"),
    ("typescript", "typed javascript"),
    ("mongodb", "nosql database"),
    ("pytest", "python testing"),
    ("django", "python web framework"),
    ("tensorflow", "deep learning framework"),
    ("redis", "in-memory cache"),
    ("terraform", "infrastructure as code"),
    ("graphql", "api query language"),
    ("jenkins", "ci/cd automation"),
    ("numpy", "numerical computing"),
    ("pandas", "data analysis"),
    ("linux", "unix operating system"),
    ("git", "version control"),
    ("rest api", "http api"),
    ("microservices", "distributed architecture"),
    ("oauth", "authentication protocol"),
    ("websocket", "real-time communication"),
    ("elasticsearch", "search engine"),
]

# Pares sem relação técnica real (rótulo esperado: negativo). Inclui
# "armadilhas" propositais (nomes foneticamente/lexicalmente parecidos, mas
# tecnologias distintas) para testar se o modelo entende significado ou só
# similaridade de string.
NEGATIVE_PAIRS: list[tuple[str, str]] = [
    ("java", "javascript"),  # armadilha: nomes parecidos, linguagens distintas
    ("c", "c#"),  # armadilha: nomes parecidos, linguagens distintas
    ("python", "excel"),
    ("react", "postgresql"),
    ("docker", "ux design"),
    ("css", "database indexing"),
    ("aws", "photoshop"),
    ("kubernetes", "photoshop"),
    ("mongodb", "excel"),
    ("github actions", "photoshop"),
    ("sql", "ux design"),
    ("redis", "excel"),
    ("terraform", "photoshop"),
    ("graphql", "ux design"),
    ("numpy", "photoshop"),
    ("linux", "excel"),
    ("oauth", "photoshop"),
]


def compute_all_similarities() -> tuple[list[dict], list[dict]]:
    """
    Calcula a similaridade real (modelo all-MiniLM-L6-v2) para cada par uma
    única vez — os thresholds são aplicados depois sobre esses valores já
    calculados, sem recomputar embeddings por threshold candidato.
    """
    positives = [
        {"job_skill": a, "resume_skill": b, "similarity": compute_similarity(a, b), "label": "positive"}
        for a, b in POSITIVE_PAIRS
    ]
    negatives = [
        {"job_skill": a, "resume_skill": b, "similarity": compute_similarity(a, b), "label": "negative"}
        for a, b in NEGATIVE_PAIRS
    ]
    return positives, negatives


def metrics_for_threshold(positives: list[dict], negatives: list[dict], threshold: float) -> dict:
    """Calcula TP/FN/FP/TN/precision/recall/F1 para um threshold candidato."""
    true_positives = sum(1 for item in positives if item["similarity"] >= threshold)
    false_negatives = len(positives) - true_positives
    false_positives = sum(1 for item in negatives if item["similarity"] >= threshold)
    true_negatives = len(negatives) - false_positives

    predicted_positive = true_positives + false_positives
    precision = true_positives / predicted_positive if predicted_positive > 0 else None

    actual_positive = true_positives + false_negatives
    recall = true_positives / actual_positive if actual_positive > 0 else None

    if precision is None or recall is None or (precision + recall) == 0:
        f1 = None
    else:
        f1 = 2 * (precision * recall) / (precision + recall)

    return {
        "threshold": threshold,
        "tp": true_positives,
        "fn": false_negatives,
        "fp": false_positives,
        "tn": true_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def changed_classifications(positives: list[dict], negatives: list[dict], threshold_a: float, threshold_b: float):
    """Lista pares que mudam de classificação (TP<->FN, TN<->FP) entre dois thresholds."""
    changes = []
    for item in positives:
        was_tp = item["similarity"] >= threshold_a
        is_tp = item["similarity"] >= threshold_b
        if was_tp != is_tp:
            changes.append({**item, "change": "FN -> TP" if is_tp else "TP -> FN"})
    for item in negatives:
        was_fp = item["similarity"] >= threshold_a
        is_fp = item["similarity"] >= threshold_b
        if was_fp != is_fp:
            changes.append({**item, "change": "TN -> FP" if is_fp else "FP -> TN"})
    return changes


def render_markdown(positives: list[dict], negatives: list[dict], all_metrics: list[dict]) -> str:
    lines = [
        "# Calibração do matching semântico — SPEC 0013",
        "",
        "Modelo: `all-MiniLM-L6-v2` (sentence-transformers). "
        f"Amostra: {len(positives)} pares positivos, {len(negatives)} pares negativos.",
        "",
        "Gerado localmente por `backend/scripts/semantic_calibration.py` — não faz parte do CI nem do deploy.",
        "",
        "## Métricas por threshold candidato",
        "",
        "| Threshold | TP | FN | FP | TN | Precision | Recall | F1 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in all_metrics:
        lines.append(
            f"| {m['threshold']:.2f} | {m['tp']} | {m['fn']} | {m['fp']} | {m['tn']} | "
            f"{_fmt(m['precision'])} | {_fmt(m['recall'])} | {_fmt(m['f1'])} |"
        )

    lines += [
        "",
        "## Pares positivos (similaridade real)",
        "",
        "| Skill da vaga | Skill do currículo | Similaridade |",
        "|---|---|---|",
    ]
    for item in sorted(positives, key=lambda x: x["similarity"], reverse=True):
        lines.append(f"| {item['job_skill']} | {item['resume_skill']} | {item['similarity']:.2f} |")

    lines += [
        "",
        "## Pares negativos (similaridade real)",
        "",
        "| Skill da vaga | Skill do currículo | Similaridade |",
        "|---|---|---|",
    ]
    for item in sorted(negatives, key=lambda x: x["similarity"], reverse=True):
        lines.append(f"| {item['job_skill']} | {item['resume_skill']} | {item['similarity']:.2f} |")

    return "\n".join(lines) + "\n"


def main() -> None:
    try:
        positives, negatives = compute_all_similarities()
    except EmbeddingUnavailableError as exc:
        print(
            "Erro: o modelo de embeddings não pôde ser carregado ou usado. "
            "Instale as dependências com `pip install -r requirements-dev.txt` "
            "e verifique sua conexão de rede.",
            file=sys.stderr,
        )
        print(f"Detalhe: {exc}", file=sys.stderr)
        sys.exit(1)

    thresholds = sorted(set(CANDIDATE_THRESHOLDS) | {SEMANTIC_SIMILARITY_THRESHOLD})
    all_metrics = [metrics_for_threshold(positives, negatives, t) for t in thresholds]

    print(f"Amostra: {len(positives)} pares positivos, {len(negatives)} pares negativos.\n")
    print(f"{'threshold':>9} {'tp':>4} {'fn':>4} {'fp':>4} {'tn':>4} {'precision':>10} {'recall':>8} {'f1':>6}")
    for m in all_metrics:
        print(
            f"{m['threshold']:>9.2f} {m['tp']:>4} {m['fn']:>4} {m['fp']:>4} {m['tn']:>4} "
            f"{_fmt(m['precision']):>10} {_fmt(m['recall']):>8} {_fmt(m['f1']):>6}"
        )

    markdown = render_markdown(positives, negatives, all_metrics)
    OUTPUT_MD_PATH.write_text(markdown, encoding="utf-8")
    print(f"\nRelatório Markdown gerado em: {OUTPUT_MD_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
