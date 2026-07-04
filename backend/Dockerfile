# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Estágio builder — instala dependências Python isoladas em /install
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# Estágio runtime — imagem final enxuta, sem ferramentas de build
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# curl é necessário apenas para o HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# tests/ não é necessário na imagem final (ver backend/.dockerignore);
# em desenvolvimento, docker-compose.yml monta ./backend como volume em /app,
# reintroduzindo tests/ para permitir `docker compose exec backend pytest tests/ -v`.

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
