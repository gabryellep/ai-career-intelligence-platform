.PHONY: test lint format format-check build-frontend up down

# Roda a suite de testes do backend com cobertura
test:
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

# Roda o lint do backend (ruff)
lint:
	cd backend && ruff check .

# Aplica formatacao automatica no backend (black)
format:
	cd backend && black .

# Verifica formatacao sem alterar arquivos (usado no CI)
format-check:
	cd backend && black --check .

# Gera o build de producao do frontend
build-frontend:
	cd frontend && npm run build

# Sobe backend, frontend e Postgres via Docker Compose
up:
	docker compose up --build

# Derruba os containers do Docker Compose
down:
	docker compose down
