"""
analyzer.py — Orquestrador da análise de compatibilidade currículo/vaga.

Este módulo é o único ponto de entrada para a lógica de análise.
AnalysisService (app/services/analysis_service.py) chama apenas analyzer.analyze().

Fluxo de análise:
    1. Extrai texto do PDF (parser.py)
    2. Normaliza e limita o texto extraído
    3. Extrai skills do currículo e da vaga (skills.py)
    4. Calcula matching e score ponderado (matcher.py)
    5. Gera recomendações de melhoria (recommender.py)
    6. Gera insights (pontos fortes, fracos e ações prioritárias)
    7. (opcional, SPEC 0011) Enriquecimento semântico via embeddings
    8. Retorna dicionário compatível com AnalyzeResponse

Matching semântico opcional (SPEC 0011):
    Se app.core.config.ENABLE_SEMANTIC_MATCHING estiver ligada, o passo 7
    tenta aproximar semanticamente skills "missing" do determinístico com
    skills "extra" do currículo (ver app/engines/semantic/hybrid.py). Nunca
    altera score, matched_skills, missing_skills, partial_skills,
    extra_skills nem match_details — apenas adiciona (quando bem-sucedido)
    as chaves semantic_score, hybrid_score e semantic_matches ao resultado.
    Qualquer falha (dependência ausente, erro do modelo) é contida e as três
    chaves simplesmente ficam ausentes do dicionário — nunca None, nunca uma
    exceção propagada.

Campo de debug (apenas em desenvolvimento):
    Se debug=True, o retorno inclui 'resume_text_preview' com os
    primeiros 500 caracteres do texto extraído do PDF.
    Nunca exposto em produção.

Metadados internos de persistência (SPEC 0004):
    O retorno inclui as chaves '_resume_text_sha256' e '_resume_text_length',
    calculadas a partir do texto já extraído nesta função — evita que o
    AnalysisService precise reprocessar o PDF (extract_text) só para obter
    o hash do texto. Essas chaves começam com "_" para sinalizar que não
    fazem parte do contrato público: AnalyzeResponse não as declara, então
    o FastAPI (response_model) as descarta automaticamente na serialização
    HTTP — o schema de POST /analyze não muda. AnalysisService remove essas
    chaves do dicionário antes de devolvê-lo ao chamador (ver
    app/services/analysis_service.py).
"""

import hashlib

from app.core.config import ENABLE_SEMANTIC_MATCHING
from app.engines.deterministic.parser import extract_text
from app.engines.deterministic.skills import extract_skills
from app.engines.deterministic.recommender import generate_recommendations
from app.engines.deterministic.matcher import analyze_skill_match, calculate_weighted_score

# Limite de caracteres do texto extraído para evitar processamento excessivo
MAX_TEXT_LENGTH = 10_000

# Resposta padrão retornada em caso de erro interno
_ERROR_RESPONSE = {
    "score": 0,
    "matched_skills": [],
    "missing_skills": [],
    "partial_skills": [],
    "extra_skills": [],
    "match_details": {},
    "recommendations": ["Não foi possível analisar o currículo."],
    "insights": {
        "strengths": [],
        "weaknesses": [],
        "priority_actions": [],
    },
    # Metadados internos (ver docstring do módulo) — sem texto extraído
    # confiável no caminho de erro, ficam nulos/zerados.
    "_resume_text_sha256": None,
    "_resume_text_length": 0,
}

# Categorias de skills para geração de insights
_SKILL_CATEGORIES = {
    "linguagens": {
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "go",
        "r",
        "rust",
        "kotlin",
        "swift",
        "php",
        "ruby",
        "scala",
        "dart",
        "elixir",
        "haskell",
        "lua",
        "perl",
        "matlab",
    },
    "backend": {
        "fastapi",
        "django",
        "flask",
        "node.js",
        "express",
        "spring boot",
        "laravel",
        "rails",
        "nestjs",
        "gin",
        "fiber",
    },
    "frontend": {"react", "next.js", "vue", "angular", "svelte", "nuxt", "gatsby", "remix", "html", "css"},
    "dados_ia": {
        "pandas",
        "numpy",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "keras",
        "matplotlib",
        "seaborn",
        "plotly",
        "jupyter",
        "spark",
        "airflow",
        "mlflow",
        "hugging face",
        "langchain",
        "xgboost",
        "lightgbm",
        "opencv",
        "machine learning",
        "deep learning",
        "nlp",
        "computer vision",
        "data science",
        "data engineering",
    },
    "devops_cloud": {
        "docker",
        "kubernetes",
        "terraform",
        "ansible",
        "jenkins",
        "github actions",
        "gitlab ci",
        "circleci",
        "ci/cd",
        "linux",
        "nginx",
        "apache",
        "prometheus",
        "grafana",
        "git",
        "aws",
        "azure",
        "gcp",
        "heroku",
        "vercel",
        "netlify",
        "cloudflare",
    },
    "banco_dados": {
        "postgresql",
        "mysql",
        "sqlite",
        "sql server",
        "oracle",
        "mariadb",
        "mongodb",
        "redis",
        "elasticsearch",
        "dynamodb",
        "cassandra",
        "firebase",
        "neo4j",
        "couchdb",
    },
    "idiomas": {"english", "espanhol", "frances", "alemao", "mandarin", "japones"},
}

_CATEGORY_LABELS = {
    "linguagens": "linguagens de programação",
    "backend": "desenvolvimento backend",
    "frontend": "desenvolvimento frontend",
    "dados_ia": "dados e inteligência artificial",
    "devops_cloud": "DevOps e cloud",
    "banco_dados": "bancos de dados",
    "idiomas": "idiomas",
}


def _generate_insights(
    resume_skills: list[str],
    job_skills: list[str],
    matched_skills: list[str],
    missing_skills: list[str],
    partial_skills: list[str],
    score: int,
) -> dict:
    """
    Gera insights sobre o perfil do candidato em relação à vaga.

    Retorna dicionário com:
        - strengths: pontos fortes do candidato
        - weaknesses: pontos de atenção
        - priority_actions: ações concretas e prioritárias (máx 5)
    """
    strengths: list[str] = []
    weaknesses: list[str] = []
    priority_actions: list[str] = []

    job_set = set(job_skills)
    matched_set = set(matched_skills)

    # --- Pontos fortes ---

    # Destaca skills matched mais relevantes por categoria
    covered_categories = []
    for category, skills in _SKILL_CATEGORIES.items():
        job_in_category = job_set & skills
        if not job_in_category:
            continue
        matched_in_category = matched_set & skills
        coverage = len(matched_in_category) / len(job_in_category)
        label = _CATEGORY_LABELS.get(category, category)
        if coverage >= 0.7:
            covered_categories.append((label, matched_in_category))

    for label, skills in covered_categories[:3]:
        skill_list = ", ".join(sorted(skills)[:3])
        strengths.append(f"Boa cobertura em {label}: {skill_list}")

    if score >= 80:
        strengths.append("Perfil altamente compatível com os requisitos da vaga")
    elif score >= 60:
        strengths.append("Perfil com boa base técnica para a vaga")

    if matched_skills:
        top = ", ".join(sorted(matched_skills)[:4])
        strengths.append(f"Skills diretamente alinhadas com a vaga: {top}")

    # --- Pontos fracos ---

    # Skills ausentes por categoria
    gap_categories = []
    for category, skills in _SKILL_CATEGORIES.items():
        job_in_category = job_set & skills
        if not job_in_category:
            continue
        matched_in_category = matched_set & skills
        coverage = len(matched_in_category) / len(job_in_category)
        label = _CATEGORY_LABELS.get(category, category)
        if coverage < 0.4:
            gap_skills = job_in_category - matched_set
            gap_categories.append((label, gap_skills))

    for label, skills in gap_categories[:2]:
        skill_list = ", ".join(sorted(skills)[:3])
        weaknesses.append(f"Gap em {label}: {skill_list}")

    if partial_skills:
        partial_list = ", ".join(sorted(partial_skills)[:3])
        weaknesses.append(f"Skills parcialmente atendidas (nível inferior ao exigido): {partial_list}")

    if score < 40:
        weaknesses.append("Compatibilidade baixa — muitos requisitos críticos não atendidos")
    elif score < 60:
        weaknesses.append("Alguns requisitos importantes da vaga ainda não estão cobertos")

    if not resume_skills:
        weaknesses.append("Não foi possível identificar skills técnicas no currículo — verifique o formato do PDF")

    # --- Ações prioritárias (máx 5) ---

    # Prioriza skills faltantes mais críticas
    top_missing = missing_skills[:3]
    for skill in top_missing:
        if skill in _SKILL_CATEGORIES.get("idiomas", set()) or "english" in skill:
            priority_actions.append(f"Informe seu nível CEFR de {skill} no currículo e comprove com certificação")
        elif skill in _SKILL_CATEGORIES.get("devops_cloud", set()):
            priority_actions.append(f"Crie e publique um projeto com {skill} no GitHub")
        else:
            priority_actions.append(f"Desenvolva um projeto prático com {skill} e adicione ao portfólio")

    # Ação para skills parciais
    if partial_skills:
        priority_actions.append(
            "Melhore e documente seu nível de inglês — informe o nível CEFR e considere certificação"
        )

    # Ação de posicionamento
    if score >= 70:
        priority_actions.append("Reposicione o currículo destacando as skills em comum com a vaga no topo")
    elif score < 60 and missing_skills:
        priority_actions.append("Priorize as 2-3 skills mais críticas antes de se candidatar")

    return {
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "priority_actions": priority_actions[:5],
    }


def _try_semantic_enrichment(skill_match: dict, score: int) -> dict | None:
    """
    Chama app.engines.semantic.hybrid.enrich_with_semantic_matching, contendo
    qualquer exceção (import lazy da dependência opcional pode falhar de
    formas não previstas por hybrid.py) — nunca propaga para analyze().

    Retorna None em caso de qualquer falha; loga apenas o tipo da exceção
    (nunca a mensagem crua, que poderia ecoar nomes de skills do currículo).
    """
    try:
        from app.engines.semantic.hybrid import enrich_with_semantic_matching

        return enrich_with_semantic_matching(skill_match, score)
    except Exception as e:
        print(f"Erro no matching semântico: {type(e).__name__}")
        return None


def analyze(
    resume_bytes: bytes,
    job_description: str,
    debug: bool = False,
) -> dict:
    """
    Orquestra a análise completa de compatibilidade entre currículo e vaga.

    Args:
        resume_bytes: Conteúdo do arquivo PDF do currículo em bytes.
        job_description: Texto da descrição da vaga.
        debug: Se True (apenas em desenvolvimento), inclui 'resume_text_preview'.

    Returns:
        Dicionário com as chaves:
            - score (int): Compatibilidade entre 0 e 100.
            - matched_skills (list[str]): Skills presentes no currículo e na vaga.
            - missing_skills (list[str]): Skills da vaga ausentes no currículo.
            - recommendations (list[str]): Recomendações de melhoria.
            - insights (dict): Pontos fortes, fracos e ações prioritárias.
            - resume_text_preview (str, opcional): Apenas quando debug=True.
    """
    try:
        # Passo 1: extrai texto do PDF
        resume_text = extract_text(resume_bytes)

        # Passo 2: limita o tamanho do texto
        resume_text = resume_text[:MAX_TEXT_LENGTH]
        job_text = job_description[:MAX_TEXT_LENGTH]

        # Passo 3: extrai skills
        resume_skills = list(extract_skills(resume_text) or [])
        job_skills = list(extract_skills(job_text) or [])

        # Passo 4: matching inteligente via matcher (suporta matching parcial)
        skill_match = analyze_skill_match(resume_skills, job_skills)
        weighted_score = calculate_weighted_score(skill_match)

        matched_skills = list(skill_match.get("matched", []))
        partial_skills = list(skill_match.get("partial", []))
        missing_skills = list(skill_match.get("missing", []))
        extra_skills = list(skill_match.get("extra", []))
        score = int(weighted_score)

        # Passo 5: gera recomendações (usa missing_skills e partial_skills do matcher)
        recommendations = list(generate_recommendations(missing_skills, score, partial_skills) or [])

        # Passo 6: gera insights (inclui partial_skills)
        insights = _generate_insights(resume_skills, job_skills, matched_skills, missing_skills, partial_skills, score)

        result = {
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "partial_skills": partial_skills,
            "extra_skills": extra_skills,
            "match_details": skill_match,
            "recommendations": recommendations,
            "insights": insights,
            "_resume_text_sha256": hashlib.sha256(resume_text.encode("utf-8")).hexdigest(),
            "_resume_text_length": len(resume_text),
        }

        if debug:
            result["resume_text_preview"] = resume_text[:500]

        # Passo 7 (SPEC 0011, opcional): enriquecimento semântico. Só roda com
        # a flag ligada; qualquer falha (dependência ausente, erro de modelo)
        # é contida aqui e nunca derruba um resultado determinístico já
        # calculado com sucesso — os três campos ficam ausentes do
        # dicionário (não None) quando desligado ou quando falha, permitindo
        # que a rota sirva o mesmo contrato de sempre (ver
        # response_model_exclude_none em app/api/v1/routes/analyze.py).
        if ENABLE_SEMANTIC_MATCHING:
            semantic_result = _try_semantic_enrichment(skill_match, score)
            if semantic_result is not None:
                result["semantic_score"] = semantic_result["semantic_score"]
                result["hybrid_score"] = semantic_result["hybrid_score"]
                result["semantic_matches"] = semantic_result["semantic_matches"]

        return result

    except Exception as e:
        # Loga apenas o tipo da exceção — nunca a mensagem crua, que poderia
        # ecoar texto do currículo ou da descrição da vaga.
        print(f"Erro no analyzer: {type(e).__name__}")
        result = dict(_ERROR_RESPONSE)
        if debug:
            result["resume_text_preview"] = ""
        return result
