"""
career_plan.py - Career Improvement Plan deterministico.

Gera um plano estruturado exclusivamente a partir de gaps reais:
missing_skills e partial_skills. Nao usa LLM, nao altera score/matching e
nao recomenda inflar curriculo com skills nao comprovadas.
"""

from app.engines.deterministic.skills import SKILL_CATEGORIES

MAX_PLAN_ITEMS = 6

_CATEGORY_LABELS = {
    "programming_languages": "linguagem de programacao",
    "backend": "backend",
    "frontend": "frontend",
    "data_ai": "dados e IA",
    "devops": "DevOps",
    "databases": "banco de dados",
    "cloud": "cloud",
    "languages": "idioma",
    "soft_skills": "pratica de engenharia",
}

_RESOURCE_BY_SKILL = {
    "docker": ["Docker Docs", "roadmap.sh Docker"],
    "kubernetes": ["Kubernetes Docs", "roadmap.sh Kubernetes"],
    "github actions": ["GitHub Actions Docs"],
    "fastapi": ["FastAPI Docs"],
    "django": ["Django Docs"],
    "flask": ["Flask Docs"],
    "node.js": ["Node.js Docs", "MDN Web Docs"],
    "react": ["React Docs", "MDN Web Docs"],
    "javascript": ["MDN JavaScript", "freeCodeCamp JavaScript"],
    "typescript": ["TypeScript Handbook", "MDN Web Docs"],
    "postgresql": ["PostgreSQL Docs"],
    "mysql": ["MySQL Docs"],
    "mongodb": ["MongoDB Docs"],
    "redis": ["Redis Docs"],
    "scikit-learn": ["scikit-learn Docs"],
    "pandas": ["pandas Docs"],
    "numpy": ["NumPy Docs"],
    "machine learning": ["scikit-learn Docs", "Hugging Face Course"],
    "deep learning": ["Hugging Face Course", "PyTorch Tutorials"],
    "nlp": ["Hugging Face Course"],
    "aws": ["AWS Skill Builder", "AWS Docs"],
    "azure": ["Microsoft Learn Azure"],
    "gcp": ["Google Cloud Docs"],
}

_RESOURCE_BY_CATEGORY = {
    "programming_languages": ["roadmap.sh", "freeCodeCamp"],
    "backend": ["roadmap.sh Backend", "documentacao oficial da tecnologia"],
    "frontend": ["MDN Web Docs", "roadmap.sh Frontend"],
    "data_ai": ["scikit-learn Docs", "Hugging Face Course"],
    "devops": ["roadmap.sh DevOps", "documentacao oficial da ferramenta"],
    "databases": ["documentacao oficial do banco", "roadmap.sh SQL"],
    "cloud": ["documentacao oficial do provedor cloud"],
    "languages": ["CEFR self-assessment grid", "recursos gratuitos de pratica do idioma"],
    "soft_skills": ["roadmap.sh", "documentacao oficial da ferramenta"],
}


def _category_for(skill: str) -> str:
    for category, skills in SKILL_CATEGORIES.items():
        if skill in skills:
            return category
    return "soft_skills"


def _resources_for(skill: str, category: str) -> list[str]:
    resources = _RESOURCE_BY_SKILL.get(skill, _RESOURCE_BY_CATEGORY.get(category, ["roadmap.sh"]))
    return list(dict.fromkeys(resources))[:3]


def _study_action(skill: str, category: str, status: str) -> str:
    if category == "languages":
        level_note = "o nivel exigido" if status == "partial" else "o nivel pedido"
        return f"Estude {skill} com foco em atingir {level_note} e registre evidencias objetivas de progresso."
    if status == "partial":
        return f"Revise {skill} com foco nos pontos que a vaga exige e compare seu nivel atual com exemplos reais."
    return f"Estude os fundamentos de {skill} pela documentacao oficial antes de aplicar em um projeto."


def _practice_action(skill: str, category: str) -> str:
    if category in {"devops", "cloud"}:
        return f"Publique um projeto pequeno usando {skill}, com README explicando arquitetura, comandos e trade-offs."
    if category == "backend":
        return f"Crie uma API pequena usando {skill}, com testes, validacao de entrada e instrucoes de execucao."
    if category == "data_ai":
        return f"Monte um notebook ou pipeline simples com {skill}, incluindo dados de exemplo, metricas e conclusoes."
    if category == "databases":
        return f"Modele um caso simples com {skill}, incluindo consultas, indices ou migracoes quando fizer sentido."
    if category == "languages":
        return f"Pratique {skill} com simulacoes de entrevista, leitura tecnica e escrita de resumos sobre projetos."
    return f"Crie um mini-projeto verificavel usando {skill} e documente o que foi implementado."


def _resume_guidance(skill: str, status: str) -> str:
    if status == "partial":
        return (
            f"Atualize o curriculo sobre {skill} apenas para refletir o nivel real ja comprovado, "
            "sem declarar dominio total."
        )
    return (
        f"Adicione {skill} ao curriculo somente depois de ter projeto, estudo documentado ou experiencia comprovavel."
    )


def _profile_guidance(skill: str) -> str:
    return (
        f"No GitHub/LinkedIn, mostre evidencias de {skill}: repositorio, README claro, decisoes tecnicas e resultados."
    )


def _build_item(skill: str, status: str) -> dict:
    category = _category_for(skill)
    return {
        "skill": skill,
        "gap_type": status,
        "focus_area": _CATEGORY_LABELS.get(category, category),
        "study": _study_action(skill, category, status),
        "practice": _practice_action(skill, category),
        "resume_guidance": _resume_guidance(skill, status),
        "profile_guidance": _profile_guidance(skill),
        "resources": _resources_for(skill, category),
    }


def generate_career_improvement_plan(
    missing_skills: list[str],
    partial_skills: list[str] | None = None,
) -> dict | None:
    """
    Gera plano de melhoria apenas quando existem gaps reais.

    missing_skills tem prioridade sobre partial_skills. Skills duplicadas
    aparecem uma unica vez, preservando essa ordem de prioridade.
    """
    missing = [skill for skill in (missing_skills or []) if skill]
    partial = [skill for skill in (partial_skills or []) if skill and skill not in missing]

    gaps = [("missing", skill) for skill in missing] + [("partial", skill) for skill in partial]
    if not gaps:
        return None

    items = [_build_item(skill, status) for status, skill in gaps[:MAX_PLAN_ITEMS]]

    return {
        "summary": "Plano deterministico gerado apenas a partir das lacunas reais desta analise.",
        "items": items,
        "honesty_note": (
            "Nao adicione uma skill ao curriculo antes de comprovar estudo, projeto ou experiencia real. "
            "Este plano nao promete emprego, entrevista ou aprovacao."
        ),
    }
