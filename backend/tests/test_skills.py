"""
test_skills.py — Testes unitários do módulo skills.py.

Testa a função extract_skills com os seguintes cenários:
1. Extração case-insensitive
2. Texto sem skills — retorna lista vazia
3. Ausência de duplicatas no resultado
4. Skills compostas (ex: "spring boot", "machine learning")
5. Word boundaries — evita falsos positivos
6. Skills com símbolos (ex: "c++", "c#", "next.js", "ci/cd")
7. Texto vazio ou apenas espaços
"""

from app.skills import extract_skills, SKILLS_DICT


# ---------------------------------------------------------------------------
# Testes de comportamento básico
# ---------------------------------------------------------------------------

def test_extract_skills_case_insensitive():
    """A extração deve funcionar independente de maiúsculas/minúsculas."""
    result_lower = extract_skills("python fastapi docker")
    result_upper = extract_skills("PYTHON FASTAPI DOCKER")
    result_mixed = extract_skills("Python FastAPI Docker")

    assert result_lower == result_upper == result_mixed
    assert "python" in result_lower
    assert "fastapi" in result_lower
    assert "docker" in result_lower


def test_extract_skills_returns_empty_for_no_skills():
    """Texto sem nenhuma skill do dicionário deve retornar lista vazia."""
    result = extract_skills("Olá, meu nome é João e gosto de cozinhar.")
    assert result == []


def test_extract_skills_returns_empty_for_empty_string():
    """String vazia deve retornar lista vazia."""
    assert extract_skills("") == []


def test_extract_skills_returns_empty_for_whitespace():
    """String com apenas espaços deve retornar lista vazia."""
    assert extract_skills("   ") == []


def test_extract_skills_no_duplicates():
    """O resultado não deve conter duplicatas mesmo que a skill apareça várias vezes."""
    text = "python python python python"
    result = extract_skills(text)
    assert len(result) == len(set(result))
    assert result.count("python") == 1


def test_extract_skills_returns_sorted_list():
    """O resultado deve ser uma lista ordenada alfabeticamente."""
    result = extract_skills("docker python aws fastapi")
    assert result == sorted(result)


# ---------------------------------------------------------------------------
# Testes de skills compostas
# ---------------------------------------------------------------------------

def test_extract_composite_skill_spring_boot():
    """Skills compostas como 'spring boot' devem ser detectadas corretamente."""
    result = extract_skills("Tenho experiência com Spring Boot e Java.")
    assert "spring boot" in result


def test_extract_composite_skill_machine_learning():
    """'machine learning' deve ser detectado como skill composta."""
    result = extract_skills("Trabalho com machine learning e deep learning.")
    assert "machine learning" in result
    assert "deep learning" in result


def test_extract_composite_skill_github_actions():
    """'github actions' deve ser detectado como skill composta."""
    result = extract_skills("Configuro pipelines com GitHub Actions.")
    assert "github actions" in result


# ---------------------------------------------------------------------------
# Testes de word boundaries — evitar falsos positivos
# ---------------------------------------------------------------------------

def test_no_false_positive_go_in_google():
    """'go' não deve ser detectado dentro de 'google'."""
    result = extract_skills("Uso google para pesquisar.")
    assert "go" not in result


def test_no_false_positive_go_in_django():
    """'go' não deve ser detectado dentro de 'django'."""
    result = extract_skills("Desenvolvo com django.")
    assert "go" not in result


def test_no_false_positive_r_in_react():
    """'r' não deve ser detectado dentro de 'react'."""
    result = extract_skills("Uso react no frontend.")
    assert "r" not in result


def test_no_false_positive_r_in_docker():
    """'r' não deve ser detectado dentro de 'docker'."""
    result = extract_skills("Uso docker para containers.")
    assert "r" not in result


# ---------------------------------------------------------------------------
# Testes de skills com símbolos
# ---------------------------------------------------------------------------

def test_extract_skill_with_plus_plus():
    """'c++' deve ser detectado corretamente."""
    result = extract_skills("Tenho experiência com C++ e sistemas embarcados.")
    assert "c++" in result


def test_extract_skill_with_hash():
    """'c#' deve ser detectado corretamente."""
    result = extract_skills("Desenvolvo aplicações em C# e .NET.")
    assert "c#" in result


def test_extract_skill_next_js():
    """'next.js' deve ser detectado corretamente."""
    result = extract_skills("Uso Next.js para renderização server-side.")
    assert "next.js" in result


def test_extract_skill_ci_cd():
    """'ci/cd' deve ser detectado corretamente."""
    result = extract_skills("Implemento pipelines de CI/CD com GitHub Actions.")
    assert "ci/cd" in result


# ---------------------------------------------------------------------------
# Teste de integridade do dicionário
# ---------------------------------------------------------------------------

def test_skills_dict_has_minimum_100_terms():
    """O SKILLS_DICT deve conter no mínimo 100 termos."""
    assert len(SKILLS_DICT) >= 100


def test_skills_dict_has_no_duplicates():
    """O SKILLS_DICT não deve conter duplicatas."""
    assert len(SKILLS_DICT) == len(set(SKILLS_DICT))


def test_skills_dict_all_lowercase():
    """Todos os termos do SKILLS_DICT devem estar em minúsculas."""
    for skill in SKILLS_DICT:
        assert skill == skill.lower(), f"Skill não está em minúsculas: '{skill}'"


# ---------------------------------------------------------------------------
# Testes de aliases e sinônimos
# ---------------------------------------------------------------------------

def test_alias_amazon_web_services_returns_aws():
    """'amazon web services' deve retornar 'aws'."""
    result = extract_skills("Experiência com Amazon Web Services e Lambda.")
    assert "aws" in result


def test_alias_postgres_returns_postgresql():
    """'postgres' deve retornar 'postgresql'."""
    result = extract_skills("Banco de dados: Postgres e Redis.")
    assert "postgresql" in result


def test_alias_postgres_sql_returns_postgresql():
    """'postgres sql' deve retornar 'postgresql'."""
    result = extract_skills("Uso Postgres SQL no dia a dia.")
    assert "postgresql" in result


def test_alias_nodejs_returns_node_js():
    """'nodejs' deve retornar 'node.js'."""
    result = extract_skills("Desenvolvedor NodeJS com Express.")
    assert "node.js" in result


def test_alias_js_returns_javascript():
    """'js' isolado deve retornar 'javascript'."""
    result = extract_skills("Habilidades: JS, CSS e HTML.")
    assert "javascript" in result


def test_alias_ts_returns_typescript():
    """'ts' isolado deve retornar 'typescript'."""
    result = extract_skills("Projeto em TS com React.")
    assert "typescript" in result


def test_alias_ci_cd_hyphen_returns_ci_cd():
    """'ci-cd' deve retornar 'ci/cd'."""
    result = extract_skills("Pipeline de CI-CD com GitHub Actions.")
    assert "ci/cd" in result


def test_alias_machine_learning_hyphen():
    """'machine-learning' deve retornar 'machine learning'."""
    result = extract_skills("Experiência com machine-learning e Python.")
    assert "machine learning" in result


def test_alias_k8s_returns_kubernetes():
    """'k8s' deve retornar 'kubernetes'."""
    result = extract_skills("Deploy em k8s com Helm.")
    assert "kubernetes" in result


def test_alias_sklearn_returns_scikit_learn():
    """'sklearn' deve retornar 'scikit-learn'."""
    result = extract_skills("Modelos com sklearn e pandas.")
    assert "scikit-learn" in result


# ---------------------------------------------------------------------------
# Testes de detecção de idioma com nível
# ---------------------------------------------------------------------------

def test_ingles_sem_nivel_retorna_english_basic():
    """'inglês' sem nível deve retornar 'english_basic'."""
    result = extract_skills("Idiomas: inglês.")
    assert "english_basic" in result
    assert "english_advanced" not in result
    assert "english_intermediate" not in result


def test_english_sozinho_retorna_english_basic():
    """'english' sozinho não deve retornar 'english_advanced'."""
    result = extract_skills("Languages: English.")
    assert "english_basic" in result
    assert "english_advanced" not in result


def test_ingles_intermediario_retorna_english_intermediate():
    """'inglês intermediário' deve retornar 'english_intermediate'."""
    result = extract_skills("Inglês intermediário (B2).")
    assert "english_intermediate" in result
    assert "english_basic" not in result
    assert "english_advanced" not in result


def test_b1_retorna_english_intermediate():
    """'B1' deve retornar 'english_intermediate'."""
    result = extract_skills("Inglês B1.")
    assert "english_intermediate" in result


def test_ingles_avancado_retorna_english_advanced():
    """'inglês avançado' deve retornar 'english_advanced'."""
    result = extract_skills("Inglês avançado.")
    assert "english_advanced" in result
    assert "english_basic" not in result
    assert "english_intermediate" not in result


def test_advanced_english_retorna_english_advanced():
    """'advanced english' deve retornar 'english_advanced'."""
    result = extract_skills("Advanced English (C1).")
    assert "english_advanced" in result


def test_c1_retorna_english_advanced():
    """'C1' deve retornar 'english_advanced'."""
    result = extract_skills("Inglês C1.")
    assert "english_advanced" in result


def test_fluent_english_retorna_english_advanced():
    """'fluent english' deve retornar 'english_advanced'."""
    result = extract_skills("Fluent English speaker.")
    assert "english_advanced" in result


def test_english_advanced_nao_retorna_basic():
    """Quando detecta avançado, não deve retornar basic."""
    result = extract_skills("Inglês avançado C2.")
    assert "english_advanced" in result
    assert "english_basic" not in result
    assert "english_intermediate" not in result
