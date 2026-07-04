"""
test_llm_providers.py — Testes de app.services.llm_providers.ollama_provider (SPEC 0014).

Nunca chama um Ollama real — monkeypatch de httpx.post simula sucesso,
timeout, erro de conexão e status HTTP de erro.
"""

import httpx
import pytest

from app.services.llm_providers.base import LLMUnavailableError
from app.services.llm_providers.ollama_provider import generate


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://localhost:11434/api/generate")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("erro simulado", request=request, response=response)

    def json(self):
        return self._json_data


def test_generate_returns_response_text_on_success(monkeypatch):
    def fake_post(url, json, timeout):
        return _FakeResponse({"response": '{"llm_summary": "ok"}'})

    monkeypatch.setattr(httpx, "post", fake_post)

    result = generate("prompt de teste")

    assert result == '{"llm_summary": "ok"}'


def test_generate_raises_llm_unavailable_on_connect_error(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.ConnectError("conexão recusada simulada")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMUnavailableError):
        generate("prompt de teste")


def test_generate_raises_llm_unavailable_on_timeout(monkeypatch):
    def fake_post(url, json, timeout):
        raise httpx.TimeoutException("timeout simulado")

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMUnavailableError):
        generate("prompt de teste")


def test_generate_raises_llm_unavailable_on_http_error_status(monkeypatch):
    def fake_post(url, json, timeout):
        return _FakeResponse({}, status_code=500)

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMUnavailableError):
        generate("prompt de teste")


def test_generate_raises_llm_unavailable_on_unexpected_response_shape(monkeypatch):
    def fake_post(url, json, timeout):
        return _FakeResponse({"unexpected_key": "sem 'response'"})

    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(LLMUnavailableError):
        generate("prompt de teste")
