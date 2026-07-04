# Contribuindo

Obrigado por considerar contribuir com o **AI Career Intelligence Platform** (repositório `ai-resume-analyzer`).

## Antes de abrir um Pull Request

Rode localmente os mesmos checks que o CI (`.github/workflows/ci.yml`) executa, para evitar surpresas:

```bash
# Backend — lint, formatação e testes com cobertura
cd backend
pip install -r requirements-dev.txt
ruff check .
black --check .
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
```

```bash
# Frontend — build de produção
cd frontend
npm run build
```

Ou, usando os atalhos do `Makefile` a partir da raiz do projeto:

```bash
make lint
make format-check
make test
make build-frontend
```

Se `black --check .` apontar arquivos para reformatar, rode `make format` (ou `black .` dentro de `backend/`) e revise o diff antes de commitar — a formatação não deve alterar nenhuma lógica.

## Fluxo de contribuição

```bash
git checkout -b feature/minha-feature
git commit -m "feat: adiciona minha feature"
git push origin feature/minha-feature
```

Depois, abra um Pull Request. O workflow de CI validará automaticamente lint, formatação, testes com cobertura (backend) e build (frontend).

## O que o CI valida

- **`backend-tests`**: `ruff check .`, `black --check .` e `pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80`.
- **`frontend-build`**: `npm ci` e `npm run build`.

## Escopo

Este projeto usa um motor de análise determinístico (sem IA generativa) — ver a seção "Motor determinístico e explicável" no [README](README.md) para o contexto completo antes de propor mudanças na lógica de score, matching ou recomendações.
