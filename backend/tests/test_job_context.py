"""
Testes do parser contextual deterministico de descricoes de vaga.
"""

from app.engines.deterministic.job_context import (
    active_job_skills,
    analyze_job_context,
    calculate_contextual_score,
)
from app.engines.deterministic.matcher import analyze_skill_match
from app.engines.deterministic.skills import extract_skills


def _requirement(context: dict, skill: str) -> dict:
    return next(item for item in context["requirements"] if item["skill"] == skill)


def test_required_must_have_skill_gets_full_weight():
    job = "Must have Python and Docker experience."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)

    assert _requirement(context, "python")["importance"] == "required"
    assert _requirement(context, "docker")["weight"] == 1.0


def test_nice_to_have_skill_gets_lower_weight():
    job = "Required: Python. Nice to have: Docker."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)
    match = analyze_skill_match(["python"], active_job_skills(context))

    assert _requirement(context, "docker")["importance"] == "optional"
    assert calculate_contextual_score(match, context) == 74


def test_no_experience_required_skill_is_ignored():
    job = "Required: Python. No experience with Docker required."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)
    match = analyze_skill_match(["python"], active_job_skills(context))

    assert _requirement(context, "docker")["importance"] == "ignored"
    assert "docker" not in active_job_skills(context)
    assert match["missing"] == []
    assert calculate_contextual_score(match, context) == 100


def test_detects_explicit_seniority_levels():
    senior = analyze_job_context("Senior backend engineer with Python.", ["python"])
    mid = analyze_job_context("Vaga para desenvolvedor pleno com React.", ["react"])
    junior = analyze_job_context("Junior developer, entry-level, with Java.", ["java"])

    assert senior["seniority"] == "senior"
    assert mid["seniority"] == "mid_level"
    assert junior["seniority"] == "junior"


def test_composite_skill_keeps_context():
    job = "Required: Java. Spring Boot would be a plus."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)

    assert "spring boot" in job_skills
    assert _requirement(context, "spring boot")["importance"] == "optional"


def test_language_level_context_is_supported():
    job = "Required: Advanced English C1. Docker is a plus."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)

    assert "english_advanced" in job_skills
    assert _requirement(context, "english_advanced")["importance"] == "required"
    assert _requirement(context, "docker")["importance"] == "optional"


def test_short_ambiguous_go_is_not_created_by_context_parser():
    job = "Let's go to market. Python is required."
    job_skills = extract_skills(job)

    context = analyze_job_context(job, job_skills)

    assert "go" not in job_skills
    assert [item["skill"] for item in context["requirements"]] == ["python"]


def test_no_recognized_skills_returns_empty_requirements_and_zero_score():
    context = analyze_job_context("Boa comunicacao e colaboracao.", [])

    assert context["requirements"] == []
    assert active_job_skills(context) == []
    assert calculate_contextual_score({"matched": [], "partial": [], "missing": []}, context) == 0
