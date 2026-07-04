"""
skills.py — Dicionário de skills técnicas e extração de skills de texto.

Organizado por categorias. SKILLS_DICT é derivado das categorias e mantém
compatibilidade total com o comportamento anterior.

Funcionalidades:
- Extração via dicionário com lookahead/lookbehind negativos
- Aliases e sinônimos (ex: "postgres" → "postgresql", "js" → "javascript")
- Detecção de idioma com nível (english_basic / english_intermediate / english_advanced)
- Sem duplicatas, tudo lowercase
"""

import re
from itertools import chain

# ---------------------------------------------------------------------------
# Categorias de Skills
# ---------------------------------------------------------------------------

SKILL_CATEGORIES: dict[str, list[str]] = {
    "programming_languages": [
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
    ],
    "backend": [
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
    ],
    "frontend": [
        "react",
        "next.js",
        "vue",
        "angular",
        "svelte",
        "nuxt",
        "gatsby",
        "remix",
        "html",
        "css",
    ],
    "data_ai": [
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
    ],
    "devops": [
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
    ],
    "databases": [
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
    ],
    "cloud": [
        "aws",
        "azure",
        "gcp",
        "heroku",
        "vercel",
        "netlify",
        "cloudflare",
    ],
    "languages": [
        # Idiomas — nomes canônicos com nível
        # A detecção real é feita via regex em _LANGUAGE_PATTERNS
        "english_basic",
        "english_intermediate",
        "english_advanced",
        "espanhol",
        "frances",
        "alemao",
        "mandarin",
        "japones",
    ],
    "soft_skills": [
        "agile",
        "scrum",
        "kanban",
        "tdd",
        "bdd",
        "rest api",
        "graphql",
        "grpc",
        "websocket",
        "microservices",
        "oauth",
        "jwt",
        "swagger",
        "postman",
        "figma",
        "jira",
    ],
}

# ---------------------------------------------------------------------------
# SKILLS_DICT — lista plana derivada das categorias
# Compatível com o comportamento anterior: lista de strings lowercase sem duplicatas
# ---------------------------------------------------------------------------

SKILLS_DICT: list[str] = sorted(set(chain.from_iterable(SKILL_CATEGORIES.values())))

# ---------------------------------------------------------------------------
# Aliases e sinônimos
# Mapeiam variações comuns para o nome canônico do SKILLS_DICT
# ---------------------------------------------------------------------------

_ALIASES: dict[str, str] = {
    # Cloud
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    # Bancos de dados
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "postgre sql": "postgresql",
    # Node.js
    "node": "node.js",
    "nodejs": "node.js",
    "node js": "node.js",
    # JavaScript / TypeScript
    "js": "javascript",
    "ts": "typescript",
    # CI/CD
    "ci cd": "ci/cd",
    "ci-cd": "ci/cd",
    # Machine Learning
    "machine-learning": "machine learning",
    "ml": "machine learning",
    # Deep Learning
    "deep-learning": "deep learning",
    "dl": "deep learning",
    # NLP
    "natural language processing": "nlp",
    # Computer Vision
    "cv": "computer vision",
    # Outros
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "sk-learn": "scikit-learn",
    "sklearn": "scikit-learn",
}

# ---------------------------------------------------------------------------
# Padrões de idioma com detecção de nível
# Ordem importa: avançado e intermediário devem ser verificados ANTES do básico
# ---------------------------------------------------------------------------

_ADVANCED_MARKERS = r"avan[cç]ado|advanced|fluent|fluente|proficient|c1|c2"
_INTERMEDIATE_MARKERS = r"intermedi[aá]rio|intermediate|b1|b2"

_LANGUAGE_PATTERNS: list[tuple[str, str]] = [
    # Inglês avançado
    (
        rf"(?:{_ADVANCED_MARKERS})\s+(?:ingl[eê]s|english)"
        rf"|(?:ingl[eê]s|english)\s+(?:{_ADVANCED_MARKERS})"
        rf"|(?:{_ADVANCED_MARKERS})\s+in\s+english"
        rf"|\b(?:c1|c2)\b",
        "english_advanced",
    ),
    # Inglês intermediário
    (
        rf"(?:{_INTERMEDIATE_MARKERS})\s+(?:ingl[eê]s|english)"
        rf"|(?:ingl[eê]s|english)\s+(?:{_INTERMEDIATE_MARKERS})"
        rf"|\b(?:b1|b2)\b",
        "english_intermediate",
    ),
    # Inglês básico (fallback — apenas se não detectou nível superior)
    (
        r"ingl[eê]s|english",
        "english_basic",
    ),
    # Outros idiomas
    (r"espanhol|espa[nñ]ol|spanish", "espanhol"),
    (r"franc[eê]s|french", "frances"),
    (r"alem[aã]o|german|deutsch", "alemao"),
    (r"mandarim|mandarin|chin[eê]s|chinese", "mandarin"),
    (r"japon[eê]s|japanese", "japones"),
]

# Skills de idioma — não devem ser detectadas via dicionário principal
_LANGUAGE_CANONICAL = {
    "english_basic",
    "english_intermediate",
    "english_advanced",
    "espanhol",
    "frances",
    "alemao",
    "mandarin",
    "japones",
}

# ---------------------------------------------------------------------------
# Skills curtas/ambíguas — não podem ser detectadas por substring simples
#
# "go", "c" e "r" são, respectivamente, uma palavra comum do inglês ("let's
# go", "go to market") e duas letras isoladas — mesmo com boundary de \w,
# qualquer ocorrência isolada dessas palavras/letras em texto comum (não
# necessariamente sobre programação) seria um falso positivo. Por isso não
# entram no laço de substring simples (excluídas via _SHORT_AMBIGUOUS_SKILLS,
# igual ao tratamento de idiomas) — só são detectadas por frases de contexto
# seguro em _SHORT_SKILL_PATTERNS.
# ---------------------------------------------------------------------------

_SHORT_AMBIGUOUS_SKILLS = {"go", "c", "r"}

_SHORT_SKILL_PATTERNS: list[tuple[str, str]] = [
    (
        r"\bgolang\b"
        r"|\bgo\s+language\b"
        r"|\bgo\s+programming\s+language\b"
        r"|\bgo\s+programming\b"
        r"|\bprogramming\s+in\s+go\b"
        r"|\blinguagem\s+go\b",
        "go",
    ),
    (
        r"\bc\s+programming\s+language\b"
        r"|\bc\s+programming\b"
        r"|\bprogramming\s+in\s+c\b"
        r"|\bc\s+language\b"
        r"|\blinguagem\s+c\b",
        "c",
    ),
    (
        r"\br\s+programming\s+language\b"
        r"|\br\s+programming\b"
        r"|\bprogramming\s+in\s+r\b"
        r"|\br\s+language\b"
        r"|\blinguagem\s+r\b",
        "r",
    ),
]


# ---------------------------------------------------------------------------
# Extração de Skills
# ---------------------------------------------------------------------------


def extract_skills(text: str) -> list[str]:
    """
    Identifica skills técnicas e idiomas presentes em um texto.

    Fluxo:
        1. Normaliza o texto (lowercase + strip).
        2. Aplica aliases/sinônimos para normalizar variações.
        3. Verifica cada skill do SKILLS_DICT (exceto idiomas) com regex.
        4. Aplica padrões de idioma com detecção de nível (avançado > intermediário > básico).
        5. Retorna lista ordenada sem duplicatas.

    Args:
        text: Texto do currículo ou da descrição da vaga.

    Returns:
        Lista de skills encontradas, sem duplicatas, em ordem alfabética.
        Retorna lista vazia se nenhuma skill for encontrada.
    """
    if not text or not text.strip():
        return []

    text_lower = text.lower().strip()

    # Passo 1: aplica aliases — substitui variações pelo nome canônico
    # Ordena por comprimento decrescente para evitar que aliases curtos
    # substituam partes de aliases mais longos (ex: "js" não deve afetar "next.js")
    for alias, canonical in sorted(_ALIASES.items(), key=lambda x: -len(x[0])):
        pattern = r"(?<![.\w])" + re.escape(alias) + r"(?![.\w])"
        text_lower = re.sub(pattern, canonical, text_lower)

    found: set[str] = set()

    # Passo 2: extração via dicionário (exclui skills de idioma — tratadas
    # separadamente — e skills curtas/ambíguas como "go"/"c"/"r", que exigem
    # contexto seguro em vez de substring simples — ver Passo 2.5)
    for skill in SKILLS_DICT:
        if skill in _LANGUAGE_CANONICAL or skill in _SHORT_AMBIGUOUS_SKILLS:
            continue
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text_lower):
            found.add(skill)

    # Passo 2.5: skills curtas/ambíguas ("go", "c", "r") — só entram por
    # frase de contexto seguro (ex.: "golang", "c programming"), nunca por
    # ocorrência isolada da palavra/letra (ver _SHORT_SKILL_PATTERNS).
    for pattern, canonical_name in _SHORT_SKILL_PATTERNS:
        if re.search(pattern, text_lower):
            found.add(canonical_name)

    # Passo 3: detecção de idioma com nível
    # Verifica avançado e intermediário antes do básico para evitar falso básico
    detected_english: str | None = None
    for pattern, canonical_name in _LANGUAGE_PATTERNS:
        if canonical_name.startswith("english"):
            if detected_english is None and re.search(pattern, text_lower):
                detected_english = canonical_name
        else:
            if re.search(pattern, text_lower):
                found.add(canonical_name)

    if detected_english:
        found.add(detected_english)

    return sorted(found)
