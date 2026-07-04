"""
Testes do Career Improvement Plan deterministico.
"""

from app.engines.deterministic.career_plan import generate_career_improvement_plan


def test_plan_with_missing_skills_creates_items_from_real_gaps_only():
    plan = generate_career_improvement_plan(["docker", "fastapi"], [])

    assert plan is not None
    assert [item["skill"] for item in plan["items"]] == ["docker", "fastapi"]
    assert all(item["gap_type"] == "missing" for item in plan["items"])


def test_plan_with_partial_skills_marks_gap_type_partial():
    plan = generate_career_improvement_plan([], ["english_advanced"])

    assert plan is not None
    assert plan["items"][0]["skill"] == "english_advanced"
    assert plan["items"][0]["gap_type"] == "partial"
    assert "nivel real" in plan["items"][0]["resume_guidance"]


def test_plan_without_gaps_returns_none():
    assert generate_career_improvement_plan([], []) is None


def test_cloud_devops_skill_gets_project_and_official_resources():
    plan = generate_career_improvement_plan(["docker"], [])
    item = plan["items"][0]

    assert item["focus_area"] == "DevOps"
    assert "README" in item["practice"]
    assert "Docker Docs" in item["resources"]


def test_backend_skill_gets_api_project():
    plan = generate_career_improvement_plan(["fastapi"], [])
    item = plan["items"][0]

    assert item["focus_area"] == "backend"
    assert "API" in item["practice"]
    assert "FastAPI Docs" in item["resources"]


def test_data_ai_skill_gets_notebook_or_pipeline_project():
    plan = generate_career_improvement_plan(["machine learning"], [])
    item = plan["items"][0]

    assert item["focus_area"] == "dados e IA"
    assert "notebook" in item["practice"]
    assert "Hugging Face Course" in item["resources"]


def test_language_skill_uses_level_and_evidence_guidance():
    plan = generate_career_improvement_plan([], ["english_advanced"])
    item = plan["items"][0]

    assert item["focus_area"] == "idioma"
    assert "nivel exigido" in item["study"]
    assert "evidencias" in item["profile_guidance"]


def test_plan_never_recommends_adding_unproven_skill_to_resume():
    plan = generate_career_improvement_plan(["postgresql"], [])
    item = plan["items"][0]

    assert "somente depois" in item["resume_guidance"]
    assert "comprov" in item["resume_guidance"]
    assert "emprego" in plan["honesty_note"]
