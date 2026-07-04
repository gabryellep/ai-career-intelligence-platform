# Checklist de deploy (SPEC 0010)

Este checklist cobre o deploy público atual (backend no Render, frontend na Vercel). Ele documenta o que já está configurado e o que deve ser conferido antes de qualquer novo deploy — não altera nenhuma variável de produção existente.

## Decisão de deploy vigente

- `ENABLE_HISTORY_API=false` em produção.
- `ENABLE_ANALYTICS_API=false` em produção.
- Ambas permanecem `false` até que autenticação real exista — ver justificativa completa em [PRIVACY.md](../PRIVACY.md#decisão-de-deploy-registrada-spec-0010-2026-07-03).
- O Histórico e o Dashboard (SPEC 0007) só são exercitados em ambiente local/dev, com as duas flags ligadas manualmente (ver [README.md](../README.md), seção "Histórico e Dashboard").
- `ENABLE_SEMANTIC_MATCHING=false` em produção (SPEC 0011) — motivo diferente das duas flags acima: não é uma questão de autenticação, é peso de deploy. `sentence-transformers` traz `torch` como dependência transitiva (centenas de MB) e fica só em `requirements-dev.txt`, nunca na imagem de produção — o plano gratuito do Render atual não comporta essa RAM adicional. Ver [PRIVACY.md](../PRIVACY.md#matching-semântico-via-embeddings-desde-a-spec-0011).
- `ENABLE_LLM_FEEDBACK=false` em produção (SPEC 0014) — motivo próprio, diferente de todas as flags acima: não é peso de dependência Python (`httpx`, usado para chamar o Ollama, já está em `requirements.txt` de produção) nem autenticação — é que **o processo Ollama não existe no ambiente de deploy atual** (Render, sem GPU, sem processo de longa duração para hospedar um LLM local). Ver [PRIVACY.md](../PRIVACY.md#feedback-textual-via-llm-local-desde-a-spec-0014).

## Variáveis de ambiente — Backend (Render)

| Variável | Valor em produção | Observação |
|---|---|---|
| `ENVIRONMENT` | `production` | Faz `get_cors_allowed_origins()` restringir a origem a `FRONTEND_ORIGIN`, em vez de `"*"` (só em `development`). |
| `FRONTEND_ORIGIN` | `https://ai-career-intelligence-platform-beta.vercel.app` | Único valor aceito pelo CORS quando `ENVIRONMENT != development`. O domínio antigo da Vercel (`https://ai-resume-analyzer-app-pi.vercel.app`) é legado e não deve ser usado em novos deploys. |
| `DATABASE_URL` | string de conexão do PostgreSQL gerenciado | Usada por `app/db/session.py` e por `alembic upgrade head`. |
| `ENABLE_HISTORY_API` | `false` | Não alterar sem revisitar a decisão acima. |
| `ENABLE_ANALYTICS_API` | `false` | Não alterar sem revisitar a decisão acima. |
| `ENABLE_SEMANTIC_MATCHING` | `false` | Não alterar sem antes adicionar `sentence-transformers` a `requirements.txt` (hoje só em `requirements-dev.txt`) e reavaliar o plano de hospedagem — ver justificativa acima. |
| `ENABLE_LLM_FEEDBACK` | `false` | Não alterar sem antes provisionar um processo Ollama acessível a partir do backend em produção — não existe hoje no deploy Render. |
| `LLM_PROVIDER` | `ollama` | Irrelevante enquanto `ENABLE_LLM_FEEDBACK=false`. |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Irrelevante enquanto `ENABLE_LLM_FEEDBACK=false`. |
| `OLLAMA_MODEL` | `llama3.1` | Irrelevante enquanto `ENABLE_LLM_FEEDBACK=false`. |

## Variáveis de ambiente — Frontend (Vercel)

| Variável | Valor em produção | Observação |
|---|---|---|
| `VITE_API_BASE_URL` | URL pública do backend no Render | Se ausente, o frontend cai para `/analyze` via proxy do Vite — só funciona em dev local. |

## Passos de deploy

1. Rodar `alembic upgrade head` contra o `DATABASE_URL` de produção antes (ou como parte) de cada deploy do backend que inclua novas migrations.
2. Confirmar que `ENVIRONMENT=production` está definido no serviço do Render — sem isso, o CORS ficaria aberto (`"*"`) por engano.
3. Confirmar que `FRONTEND_ORIGIN` aponta para o domínio atual da Vercel.
4. Confirmar que `ENABLE_HISTORY_API` e `ENABLE_ANALYTICS_API` continuam `false`, a menos que a decisão registrada em [PRIVACY.md](../PRIVACY.md) tenha sido formalmente revisitada.
5. Rodar a suíte de testes do backend (`pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80`) e `npm run build` no frontend antes de promover o deploy — ambos já cobertos pelo CI (`.github/workflows/ci.yml`).

## Verificação pós-deploy (isolamento de sessão)

Mesmo com as APIs de histórico/analytics desligadas, `POST /analyze` sempre grava `session_id`. Para confirmar que o isolamento por `X-Session-Id` continua funcionando após um deploy (útil para quando as flags forem eventualmente revisitadas):

1. Fazer duas análises com `X-Session-Id` diferentes (ou em duas abas anônimas distintas, que geram UUIDs distintos via `localStorage`).
2. Ligar temporariamente `ENABLE_HISTORY_API=true` em um ambiente de teste (nunca em produção sem revisitar a decisão) e confirmar via `GET /api/v1/analyses` que cada sessão só enxerga suas próprias análises.

## Rollback

Como não há autenticação real nem estado além do banco, o rollback de qualquer regressão relacionada a histórico/analytics é imediato: reverter `ENABLE_HISTORY_API`/`ENABLE_ANALYTICS_API` para `false` (já é o padrão) ou reverter o deploy do backend para a revisão anterior — nenhuma migração de dados é necessária, pois os endpoints de leitura não têm efeito colateral.

## Pendências para autenticação real

Antes de considerar ligar `ENABLE_HISTORY_API`/`ENABLE_ANALYTICS_API` em produção, faltam:

- autenticação real de usuário (login, JWT ou equivalente) — `X-Session-Id` não autentica ninguém, apenas isola por navegador;
- expiração e revogação de sessão;
- rate limiting nos endpoints de leitura e no `POST /analyze`;
- uma política de retenção/exclusão de dados vinculada a uma conta real (ver [PRIVACY.md](../PRIVACY.md)).

## Pendências para matching semântico em produção

Antes de considerar ligar `ENABLE_SEMANTIC_MATCHING` em produção, faltam:

- adicionar `sentence-transformers` a `requirements.txt` (hoje intencionalmente só em `requirements-dev.txt`);
- reavaliar o plano de hospedagem do Render (RAM/disco) para comportar `torch` + os pesos do modelo (~90 MB) sem piorar o cold start já existente no plano gratuito;
- opcionalmente, medir o impacto real de latência por requisição antes de expor a flag publicamente.

## Pendências para feedback via LLM em produção

`ENABLE_LLM_FEEDBACK` é uma ferramenta local/dev/demo — **Ollama não faz parte do deploy Render**, assim como o Histórico/Dashboard e o matching semântico. Antes de considerar produção, faltam:

- provisionar um processo Ollama acessível pelo backend em produção (hospedagem própria, já que o plano gratuito do Render não roda processos adicionais de longa duração nem tem GPU);
- reavaliar custo computacional real (CPU/RAM) de rodar um modelo como `llama3.1` de forma sustentada, não apenas local/pontual;
- medir o impacto de latência por requisição (o timeout atual de 20s prioriza não travar `/analyze`, mas em produção isso significa uma fração de requisições sem feedback de LLM caso o modelo esteja sob carga);
- reforçar a mitigação de conteúdo do LLM (hoje só por instrução de prompt — nunca prometer emprego/aprovação, nunca inventar skills) com alguma validação adicional, se o volume de uso justificar.
