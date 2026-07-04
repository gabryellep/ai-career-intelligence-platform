# docs/images/

Pasta reservada para as imagens usadas na seção "Screenshots" do README principal.

Assim que as imagens reais forem capturadas, adicione os arquivos com estes nomes exatos para que os placeholders do `README.md` passem a exibi-las automaticamente:

| Arquivo | Conteúdo esperado | Formato sugerido |
|---|---|---|
| `home.png` | Tela inicial (upload de currículo + campo de descrição da vaga) | PNG, 1280×800px |
| `result.png` | Tela de resultado (score, skills, insights, recomendações) | PNG, 1280×800px |
| `dashboard.png` | Aba "Histórico e Dashboard" com pelo menos 2–3 análises de exemplo já processadas | PNG, 1280×800px |
| `analytics.png` | Cards de analytics agregada (score médio, total de análises, skills mais faltantes) | PNG, 1280×800px |
| `llm-feedback.png` | Resposta de `POST /analyze` com `llm_summary`/`llm_improvement_plan` visíveis (Ollama local ligado — ver [seção "Feedback textual via LLM local" do README](../../README.md#feedback-textual-via-llm-local-opcional-spec-0014)) | PNG, 1280×800px |
| `architecture.png` | Diagrama de arquitetura em imagem (opcional, complementar ao diagrama Mermaid já existente no README) | PNG |
| `demo.gif` | GIF curto (30–60s) do fluxo completo: upload → análise → resultado | GIF, ≤5MB |

## Checklist de captura

- [ ] `home.png`
- [ ] `result.png`
- [ ] `dashboard.png`
- [ ] `analytics.png`
- [ ] `llm-feedback.png`
- [ ] `architecture.png`
- [ ] `demo.gif`

## Como capturar (instruções)

1. Suba o projeto localmente com Docker Compose (`cp .env.example .env && docker compose up --build`) — ver seção "Como rodar com Docker" do README.
2. Para `home.png`/`result.png`: use um currículo **fictício** (ex.: gere um PDF simples com um nome genérico como "João da Silva" ou use um template de exemplo sem dados reais de ninguém) e uma descrição de vaga também fictícia. **Nunca** use um currículo real (seu ou de terceiros).
3. Para `dashboard.png`/`analytics.png`: ligue `ENABLE_HISTORY_API=true` e `ENABLE_ANALYTICS_API=true` no seu `.env` local (não no `.env.example`), rode 2–3 análises com os mesmos dados sintéticos do passo 2, e capture a aba "Histórico e Dashboard".
4. Para `llm-feedback.png`: instale o [Ollama](https://ollama.com/), rode `ollama pull llama3.1`, ligue `ENABLE_LLM_FEEDBACK=true` no seu `.env` local, refaça uma análise e capture a resposta (via Swagger `/docs`, `curl`, ou a interface, se exibir os campos) mostrando `llm_summary` e os demais campos.
5. Para `architecture.png`: opcional — um diagrama exportado de uma ferramenta de diagramação (ex.: Excalidraw, draw.io), complementar ao diagrama Mermaid já existente no corpo do README.
6. Para `demo.gif`: grave a tela (ex.: com uma ferramenta de gravação de tela leve) fazendo o fluxo completo do "Demo flow" descrito no README, usando os mesmos dados sintéticos.

## Regra inegociável

**Nenhuma imagem capturada pode conter dados pessoais reais** — nem seu currículo real, nem de qualquer outra pessoa, nem uma vaga real copiada de um site de emprego com informações identificáveis de uma empresa específica (prefira uma descrição de vaga genérica/sintética). Isso vale para todos os arquivos do checklist acima, sem exceção.

Nenhuma dessas imagens existe ainda — esta pasta e este arquivo servem apenas para reservar o caminho (`docs/images/`) usado nos placeholders do README, evitando links quebrados até que os arquivos reais sejam adicionados.
