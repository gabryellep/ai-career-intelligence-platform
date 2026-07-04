"""
job_context.py - Leitura contextual deterministica da descricao da vaga.

Classifica skills ja extraidas da vaga por importancia, sem LLM:
- required: requisito obrigatorio ou requisito sem marcador explicito
- optional: diferencial/desejavel/nice-to-have, com peso menor no score
- ignored: mencoes negadas ("nao e necessario", "no experience required")

O modulo nao extrai novas skills. Ele apenas interpreta o contexto das skills
que skills.py ja reconheceu, mantendo o dicionario tecnico como fonte unica.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.engines.deterministic.skills import SKILL_CATEGORIES
from app.engines.deterministic.skills import _ALIASES  # noqa: PLC2701

REQUIRED_WEIGHT = 1.0
OPTIONAL_WEIGHT = 0.35

_OPTIONAL_MARKERS = (
    "nice to have",
    "nice-to-have",
    "plus",
    "bonus",
    "preferred",
    "preferable",
    "would be a plus",
    "differential",
    "desirable",
    "desejavel",
    "diferencial",
    "sera um diferencial",
    "seria um diferencial",
    "preferencial",
)

_REQUIRED_MARKERS = (
    "required",
    "requirement",
    "mandatory",
    "must have",
    "must-have",
    "must",
    "need",
    "needs",
    "essential",
    "requisito obrigatorio",
    "requisitos obrigatorios",
    "obrigatorio",
    "obrigatoria",
    "necessario",
    "necessaria",
    "essencial",
    "exigido",
    "exigida",
)

_NEGATION_MARKERS = (
    "not required",
    "not mandatory",
    "no experience required",
    "no experience with",
    "no prior experience required",
    "no prior experience with",
    "without experience required",
    "no need",
    "is not required",
    "are not required",
    "nao e necessario",
    "nao e necessaria",
    "nao necessario",
    "nao necessaria",
    "nao precisa",
    "nao exigido",
    "nao exigida",
    "sem experiencia obrigatoria",
    "sem experiencia obrigatorio",
    "sem experiencia com",
    "sem necessidade",
)

_SENIORITY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("principal", r"\bprincipal\b"),
    ("staff", r"\bstaff\b"),
    ("lead", r"\blead\b|\btech lead\b"),
    ("senior", r"\bsenior\b|\bsenioridade senior\b|\bsenior-level\b"),
    ("mid_level", r"\bpleno\b|\bmid[-\s]?level\b|\bmid\b"),
    ("junior", r"\bjunior\b|\bjr\b|\bentry[-\s]?level\b"),
    ("intern", r"\bestagio\b|\bestagiario\b|\binternship\b|\bintern\b"),
)


@dataclass(frozen=True)
class JobRequirement:
    """Representa uma skill da vaga com contexto suficiente para explicar o score."""

    skill: str
    importance: str
    weight: float
    category: str
    evidence: str


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def _split_evidence(text: str) -> list[str]:
    normalized = _normalize_text(text)
    parts = re.split(r"[\n\r.;!?]+", normalized)
    return [part.strip(" -:\t") for part in parts if part.strip(" -:\t")]


def _skill_terms(skill: str) -> list[str]:
    terms = {skill.replace("_", " ")}
    terms.update(alias for alias, canonical in _ALIASES.items() if canonical == skill)

    if skill.startswith("english_"):
        terms.update({"english", "ingles", "advanced english", "intermediate english", "basic english"})
    elif skill == "node.js":
        terms.update({"node", "nodejs", "node js"})
    elif skill == "ci/cd":
        terms.update({"ci cd", "ci-cd"})

    return sorted((_normalize_text(term) for term in terms), key=len, reverse=True)


def _has_term(text: str, term: str) -> bool:
    if not term:
        return False
    return re.search(r"(?<![\w.])" + re.escape(term) + r"(?![\w.])", text) is not None


def _find_evidence(skill: str, evidences: list[str]) -> str:
    terms = _skill_terms(skill)
    for evidence in evidences:
        if any(_has_term(evidence, term) for term in terms):
            return evidence
    return ""


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _category_for(skill: str) -> str:
    for category, skills in SKILL_CATEGORIES.items():
        if skill in skills:
            return category
    return "uncategorized"


def _classify_importance(evidence: str) -> str:
    if _contains_any(evidence, _NEGATION_MARKERS):
        return "ignored"
    if _contains_any(evidence, _OPTIONAL_MARKERS):
        return "optional"
    return "required"


def detect_seniority(job_description: str) -> str | None:
    """Detecta senioridade explicita na descricao da vaga, quando existir."""
    normalized = _normalize_text(job_description)
    for seniority, pattern in _SENIORITY_PATTERNS:
        if re.search(pattern, normalized):
            return seniority
    return None


def analyze_job_context(job_description: str, job_skills: list[str]) -> dict:
    """
    Classifica as skills extraidas da vaga de acordo com o texto ao redor.

    Skills sem evidencia localizada permanecem como required para preservar o
    comportamento historico: se o dicionario encontrou a skill na vaga, ela
    conta como requisito salvo quando houver marcador explicito de negacao.
    """
    evidences = _split_evidence(job_description)
    requirements: list[JobRequirement] = []

    for skill in sorted(set(job_skills or [])):
        evidence = _find_evidence(skill, evidences)
        importance = _classify_importance(evidence)
        if importance == "ignored":
            weight = 0.0
        elif importance == "optional":
            weight = OPTIONAL_WEIGHT
        else:
            weight = REQUIRED_WEIGHT

        requirements.append(
            JobRequirement(
                skill=skill,
                importance=importance,
                weight=weight,
                category=_category_for(skill),
                evidence=evidence,
            )
        )

    return {
        "requirements": [
            {
                "skill": requirement.skill,
                "importance": requirement.importance,
                "weight": requirement.weight,
                "category": requirement.category,
                "evidence": requirement.evidence,
            }
            for requirement in requirements
        ],
        "seniority": detect_seniority(job_description),
    }


def active_job_skills(job_context: dict) -> list[str]:
    """Retorna skills que entram no matching, excluindo mencoes negadas."""
    return [
        requirement["skill"]
        for requirement in job_context.get("requirements", [])
        if requirement.get("importance") != "ignored"
    ]


def calculate_contextual_score(match_result: dict, job_context: dict) -> int:
    """
    Calcula score com pesos por importancia da vaga.

    Mantem a pontuacao historica por status:
    - matched = 100% do peso da skill
    - partial = 50% do peso da skill
    - missing = 0
    """
    weights = {
        requirement["skill"]: float(requirement.get("weight", REQUIRED_WEIGHT))
        for requirement in job_context.get("requirements", [])
        if requirement.get("importance") != "ignored"
    }

    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0

    matched = set(match_result.get("matched", []))
    partial = set(match_result.get("partial", []))

    points = sum(weights.get(skill, REQUIRED_WEIGHT) for skill in matched)
    points += sum(weights.get(skill, REQUIRED_WEIGHT) * 0.5 for skill in partial)

    return round((points / total_weight) * 100)
