"""
test_embedding_service.py — Testes do serviço de embeddings (SPEC 0011).

Não baixa nem carrega o modelo real (sentence-transformers) — simula a
ausência da dependência via monkeypatch de builtins.__import__, garantindo
que o teste de fallback funcione da mesma forma independentemente de a
biblioteca estar de fato instalada no ambiente que roda a suíte.
"""

import builtins

import pytest

import app.engines.semantic.embedding_service as embedding_service
from app.engines.semantic.embedding_service import EmbeddingUnavailableError, compute_similarity


@pytest.fixture(autouse=True)
def _reset_model_singleton():
    """Garante que cada teste parte de um estado limpo do singleton do modelo."""
    embedding_service._model = None
    yield
    embedding_service._model = None


def test_compute_similarity_raises_when_dependency_missing(monkeypatch):
    """
    Simula sentence-transformers ausente (ImportError) — compute_similarity
    deve levantar EmbeddingUnavailableError, nunca um ImportError cru nem
    outro erro não tratado.
    """
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("simulado: sentence-transformers não instalado")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(EmbeddingUnavailableError):
        compute_similarity("python", "java")


def test_compute_similarity_raises_when_model_fails_to_load(monkeypatch):
    """Simula uma falha ao carregar o modelo (dependência presente, mas modelo indisponível)."""

    class _FakeSentenceTransformerModule:
        class SentenceTransformer:
            def __init__(self, model_name):
                raise RuntimeError("simulado: falha ao carregar pesos do modelo")

    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", _FakeSentenceTransformerModule)

    with pytest.raises(EmbeddingUnavailableError):
        compute_similarity("python", "java")


def test_compute_similarity_raises_when_encode_fails(monkeypatch):
    """Simula um modelo que carrega com sucesso mas falha ao calcular embeddings."""

    class _FakeModel:
        def encode(self, terms):
            raise RuntimeError("simulado: falha durante a inferência")

    class _FakeSentenceTransformerModule:
        def SentenceTransformer(model_name):
            return _FakeModel()

    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", _FakeSentenceTransformerModule)

    with pytest.raises(EmbeddingUnavailableError):
        compute_similarity("python", "java")


def test_compute_similarity_returns_float_with_working_stub(monkeypatch):
    """Com um stub funcional, compute_similarity retorna um float entre -1 e 1 (cosseno)."""

    class _FakeModel:
        def encode(self, terms):
            # Vetores idênticos para as duas strings -> similaridade de cosseno 1.0
            return [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]

    class _FakeSentenceTransformerModule:
        def SentenceTransformer(model_name):
            return _FakeModel()

    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", _FakeSentenceTransformerModule)

    similarity = compute_similarity("python", "python")

    assert isinstance(similarity, float)
    assert similarity == pytest.approx(1.0)


def test_model_is_cached_after_first_successful_load(monkeypatch):
    """O modelo carregado com sucesso deve ser reaproveitado (singleton), sem recarregar."""
    load_count = {"count": 0}

    class _FakeModel:
        def encode(self, terms):
            return [[1.0, 0.0], [0.0, 1.0]]

    class _FakeSentenceTransformerModule:
        def SentenceTransformer(model_name):
            load_count["count"] += 1
            return _FakeModel()

    monkeypatch.setitem(__import__("sys").modules, "sentence_transformers", _FakeSentenceTransformerModule)

    compute_similarity("python", "java")
    compute_similarity("docker", "kubernetes")

    assert load_count["count"] == 1
