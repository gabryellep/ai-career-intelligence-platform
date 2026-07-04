# docs/images/

Pasta com imagens usadas na seção "Screenshots" do README principal.

As capturas versionadas usam apenas dados sintéticos e uma resposta de análise controlada, sem currículo real, sem vaga real identificável e sem dados pessoais.

| Arquivo | Conteúdo esperado | Formato sugerido |
|---|---|---|
| `home.png` | Tela inicial (upload de currículo + campo de descrição da vaga) | PNG |
| `result.png` | Tela de resultado com score, skills, insights, recomendações e Career Improvement Plan | PNG |
| `dashboard.png` | Aba "Histórico e Dashboard" em demo pública, exibindo estado desativado quando as flags estão off | PNG |
| `demo.gif` | GIF curto do fluxo sintético: tela inicial → formulário preenchido → resultado | GIF |
| `analytics.png` | Cards de analytics agregada em ambiente local/dev com flags ligadas | PNG |
| `llm-feedback.png` | Resposta de `POST /analyze` com `llm_summary`/`llm_improvement_plan` visíveis em ambiente local com Ollama ligado | PNG |
| `architecture.png` | Diagrama de arquitetura em imagem (opcional, complementar ao diagrama Mermaid já existente no README) | PNG |

## Checklist de captura

- [x] `home.png`
- [x] `result.png`
- [x] `dashboard.png`
- [x] `demo.gif`
- [ ] `analytics.png`
- [ ] `llm-feedback.png`
- [ ] `architecture.png`

## Como capturar (instruções)

1. Suba o projeto localmente com Docker Compose (`cp .env.example .env && docker compose up --build`) — ver seção "Como rodar com Docker" do README.
2. Para `home.png`/`result.png`: use um currículo **fictício** (ex.: gere um PDF simples com um nome genérico como "João da Silva" ou use um template de exemplo sem dados reais de ninguém) e uma descrição de vaga também fictícia. **Nunca** use um currículo real (seu ou de terceiros).
3. Para `dashboard.png`/`analytics.png`: ligue `ENABLE_HISTORY_API=true` e `ENABLE_ANALYTICS_API=true` no seu `.env` local (não no `.env.example`), rode 2–3 análises com os mesmos dados sintéticos do passo 2, e capture a aba "Histórico e Dashboard".
4. Para `llm-feedback.png`: instale o [Ollama](https://ollama.com/), rode `ollama pull llama3.1`, ligue `ENABLE_LLM_FEEDBACK=true` no seu `.env` local, refaça uma análise e capture a resposta (via Swagger `/docs`, `curl`, ou a interface, se exibir os campos) mostrando `llm_summary` e os demais campos.
5. Para `architecture.png`: opcional — um diagrama exportado de uma ferramenta de diagramação (ex.: Excalidraw, draw.io), complementar ao diagrama Mermaid já existente no corpo do README.
6. Para `demo.gif`: grave a tela (ex.: com uma ferramenta de gravação de tela leve) fazendo o fluxo completo descrito no README, usando os mesmos dados sintéticos.

## Artefatos gerados nesta fase

- `home.png`, `result.png` e `dashboard.png` foram capturados localmente em viewport desktop usando Playwright + Chrome.
- `demo.gif` foi gerado a partir de frames sintéticos do fluxo principal.
- `analytics.png` e `llm-feedback.png` permanecem pendentes de propósito: dependem de flags locais/dev (`ENABLE_ANALYTICS_API=true`, `ENABLE_HISTORY_API=true`, `ENABLE_LLM_FEEDBACK=true`) e não devem ser apresentados como comportamento da demo pública.

## Regra inegociável

**Nenhuma imagem capturada pode conter dados pessoais reais** — nem seu currículo real, nem de qualquer outra pessoa, nem uma vaga real copiada de um site de emprego com informações identificáveis de uma empresa específica (prefira uma descrição de vaga genérica/sintética). Isso vale para todos os arquivos do checklist acima, sem exceção.

Antes de substituir qualquer captura, revise se nomes, e-mails, telefones, empresas, links e descrições de vaga são fictícios. Em dúvida, refaça a imagem com dados explicitamente sintéticos.
