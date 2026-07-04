# Detalhes técnicos — AI Career Intelligence Platform

Este documento reúne o detalhamento técnico que antes vivia no `README.md` principal — motor determinístico, matching semântico, feedback via LLM local, decisões de arquitetura, API completa, testes/CI e variáveis de ambiente. O README principal ficou enxuto e voltado a apresentação; este arquivo é a referência técnica completa, incluindo o histórico de decisões por Spec de desenvolvimento.

---

## Sumário

- [Motor determinístico — como o score é calculado](#motor-determinístico--como-o-score-é-calculado)
- [Matching semântico via embeddings (opcional)](#matching-semântico-via-embeddings-opcional)
- [Feedback textual via LLM local (opcional)](#feedback-textual-via-llm-local-opcional)
- [Decisões técnicas](#decisões-técnicas)
- [API completa](#api-completa)
- [Testes e CI](#testes-e-ci)
- [Docker — comandos úteis](#docker--comandos-úteis)
- [Histórico e Dashboard — detalhes](#histórico-e-dashboard--detalhes)
- [Variáveis de ambiente](#variáveis-de-ambiente)

---

## Motor determinístico — como o score é calculado

O motor (`app/engines/deterministic/`) extrai texto do PDF (PyMuPDF), identifica skills técnicas via regex + dicionário (100+ termos), aplica aliases/sinônimos, compara com a vaga e calcula um score ponderado — sem nenhum modelo de machine learning.

### Extração e aliases

Currículos e vagas usam termos diferentes para a mesma tecnologia. Exemplos de normalização:

| Termo encontrado | Skill canônica |
|---|---|
| Amazon Web Services | AWS |
| Postgres / Postgres SQL | PostgreSQL |
| NodeJS | Node.js |
| JS / TS | JavaScript / TypeScript |
| K8s | Kubernetes |
| Sklearn | Scikit-learn |

Skills muito curtas ou ambíguas ("go", "c", "r") não são detectadas por substring simples — exigem contexto seguro (ex.: "Golang", "Go language", "C programming", "R language") para evitar falsos positivos como "go" dentro de "Django", "Google" ou "goals".

### Detecção de idiomas

| Texto encontrado | Interpretação |
|---|---|
| inglês / english | english_basic |
| inglês intermediário / B1 / B2 | english_intermediate |
| inglês avançado / fluent / C1 / C2 | english_advanced |

### Matching e score

Skills são classificadas em **encontradas**, **faltantes**, **parcialmente atendidas** (ex.: inglês em nível inferior ao exigido) e **extras** (skills do currículo não pedidas pela vaga).

```text
Skill atendida completamente = 1.0 ponto
Skill parcialmente atendida  = 0.5 ponto
Skill ausente                = 0 ponto

score = round(pontos_obtidos / total_de_skills_exigidas * 100)
```

Exemplo: vaga pede Python, Docker, AWS e inglês avançado; currículo tem Python e inglês intermediário → `(1.0 + 0.5) / 4 * 100 = 38`.

### Contexto da descrição da vaga

Antes do matching final, a descrição da vaga passa por uma camada determinística que classifica cada skill já extraída como `required`, `optional` ou `ignored`. Marcadores como "must have", "required", "obrigatório" mantêm peso `1.0`; marcadores como "nice to have", "plus", "desejável" e "diferencial" entram com peso `0.35`; menções negadas como "not required", "no experience required" e "não é necessário" saem do matching.

O mesmo parser detecta senioridade explícita (`junior`, `pleno/mid-level`, `senior`, `lead`, `staff`, `principal`, `intern`) e inclui a explicação em `match_details.job_context`, junto de categoria, peso e trecho de evidência por skill. Essa camada não usa LLM, não cria novas skills e preserva o comportamento histórico quando a vaga não traz marcadores contextuais.

Recomendações e insights (pontos fortes/fracos/próximos passos) são gerados a partir das skills faltantes/parciais e do score geral — sempre texto determinístico, nunca gerado por modelo de linguagem.

### Career Improvement Plan

Quando existem `missing_skills` ou `partial_skills`, o backend adiciona `career_improvement_plan` à resposta de `POST /analyze`. O plano é determinístico e contém itens por skill, separando estudo, prática em projeto, orientação de currículo, GitHub/LinkedIn e recursos de aprendizagem. Ele nunca cria skills novas: cada item nasce exclusivamente de uma skill faltante ou parcialmente atendida já calculada pelo matching.

O campo fica ausente quando não há lacunas reais. A orientação de currículo sempre reforça que uma skill só deve ser adicionada depois de estudo, projeto ou experiência comprovável. O plano não promete emprego, entrevista, aprovação ou contratação, e não usa LLM como fonte de verdade.

---

## Matching semântico via embeddings (opcional)

Camada opcional (`app/engines/semantic/`) que usa [`sentence-transformers`](https://www.sbert.net/) (`all-MiniLM-L6-v2`, ~90 MB, roda em CPU) para aproximar skills que o dicionário de aliases não cobre (ex.: "containers" ≈ "Docker").

**Como funciona**: só entra em ação para skills já classificadas como faltantes; procura, entre as skills extras do currículo, a de maior similaridade de cosseno; acima do threshold, conta como aproximação semântica.

- `semantic_score`: mesma fórmula de peso do score determinístico, tratando cada aproximação semântica como "parcial" (peso 0.5).
- `hybrid_score`: 70% score determinístico + 30% semantic_score.
- `semantic_matches`: lista (máx. 10 itens) mostrando exatamente qual skill foi aproximada de qual, e com que similaridade — nunca uma caixa-preta.

**Calibração do threshold**: o valor inicial (0.70) tinha recall muito baixo — validado com 9 pares de teste, nenhum par de aproximação esperada cruzava o threshold. Uma calibração posterior, com uma amostra de 44 pares rotulados (27 positivos + 17 negativos, incluindo armadilhas lexicais como "java" vs. "javascript"), mediu precision/recall/F1 para 5 thresholds candidatos (0.50 a 0.70). Resultado: **zero falsos positivos em todos os candidatos testados**, com o maior falso positivo candidato em 0.40 de similaridade — o threshold foi reduzido para **0.50**, dobrando o recall (0.07 → 0.33) sem custar precisão. Scripts de reprodução: `backend/scripts/semantic_demo.py` e `backend/scripts/semantic_calibration.py` (exigem `pip install -r requirements-dev.txt`; não rodam no CI).

**Por que fica desligada em produção**: a dependência (`sentence-transformers`, que traz `torch` transitivamente — centenas de MB) fica só em `requirements-dev.txt`, nunca na imagem Docker de produção. O plano gratuito de hospedagem atual não comporta essa RAM adicional. Ligar a flag sem a dependência instalada não quebra nada — o fallback garante que a análise responde normalmente, apenas sem o enriquecimento semântico.

**Contrato de API**: `semantic_score`, `hybrid_score` e `semantic_matches` são campos opcionais e aditivos — com a flag desligada (padrão), a resposta de `POST /analyze` é idêntica à versão sem essa camada.

---

## Feedback textual via LLM local (opcional)

Camada opcional (`app/services/llm_feedback_service.py`) que usa um LLM open-source rodando **localmente via [Ollama](https://ollama.com/)** para reescrever o resultado em linguagem mais natural. **O LLM nunca decide nada** — só lê o resultado já calculado (score, skills, insights) e gera texto explicativo; `score`, `matched_skills`, `missing_skills` e os campos semânticos continuam sendo calculados exclusivamente pelo motor determinístico/semântico.

**Como rodar localmente:**

```bash
# 1. Instalar o Ollama: https://ollama.com/download
ollama pull llama3.1

# 2. No seu .env (backend)
ENABLE_LLM_FEEDBACK=true
OLLAMA_MODEL=llama3.1                    # opcional, já é o padrão
OLLAMA_BASE_URL=http://localhost:11434   # opcional, já é o padrão
```

Com a flag ligada, `POST /analyze` passa a incluir `llm_summary` (parágrafo curto), `llm_improvement_plan`, `llm_study_suggestions` e `llm_resume_tips` (até 5 itens cada) — visíveis **no JSON de resposta** (Swagger, `curl`, DevTools); o frontend não renderiza esses campos na interface.

**O que é enviado ao LLM (e o que nunca é)**: apenas dados já estruturados — score, skills, insights e, se existirem, semantic_score/hybrid_score. Nunca o PDF, o texto do currículo/vaga, hashes ou `session_id`.

**Fallback**: se a flag estiver desligada, o Ollama não estiver acessível, a chamada estourar o timeout (20s) ou a resposta não vier em JSON válido no formato esperado, `POST /analyze` responde normalmente, apenas sem os campos de LLM — nunca quebra.

**Por que fica desligada em produção**: diferente do matching semântico, aqui o problema não é peso de dependência Python (`httpx` já está em `requirements.txt` de produção) — é que **Ollama é um processo externo que não existe no ambiente de deploy atual** (sem GPU, sem processo de longa duração).

**Custo e desempenho**: sem custo de API (roda inteiramente na sua máquina), mas com custo computacional real (CPU/RAM/energia). Sem GPU, modelos como `llama3.1` podem levar vários segundos por resposta.

**Limitação reconhecida**: não há verificação automática de que o LLM não "alucine" uma skill fora da lista fornecida — a mitigação é só por instrução de prompt (nunca inventar skills, nunca prometer emprego/aprovação), não por validação estrutural.

---

## Decisões técnicas

- **Motor determinístico em vez de LLM na v1**: prioriza explicabilidade, testabilidade e independência de APIs pagas.
- **Score ponderado (1.0 / 0.5 / 0)** em vez de correspondência binária: reflete melhor situações como nível de idioma parcialmente atendido.
- **Persistência via SQLAlchemy síncrono, não assíncrono**: o volume de tráfego esperado não justifica a complexidade de `AsyncSession`/`asyncpg`.
- **Falha de banco nunca quebra `/analyze`**: se o PostgreSQL estiver indisponível, a persistência falha de forma controlada e a análise já computada é retornada normalmente.
- **Nunca persistir PDF ou texto bruto**: apenas hashes (SHA-256), comprimentos, skills extraídas e o resultado estruturado são armazenados.
- **Histórico e analytics atrás de feature flags separadas** (`ENABLE_HISTORY_API`, `ENABLE_ANALYTICS_API`): sem autenticação real, ambos são isolados por sessão anônima, não por pessoa — por isso ficam desligados em produção até existir autenticação. Flags separadas porque analytics expõe só números agregados, um perfil de risco diferente do histórico granular.
- **Isolamento por sessão anônima via `X-Session-Id`, não cookies**: um UUID gerado no frontend (`localStorage`), enviado como header. Evita lidar com `SameSite`/`Secure`/CORS de cookies entre domínios diferentes. Não é um mecanismo de autenticação real.
- **Ordenação de listagens por `created_at DESC, id DESC`, não só `created_at DESC`**: análises criadas em sucessão rápida podem receber o mesmo timestamp até o microssegundo; o `id` desempata sem introduzir nova coluna.
- **Matching semântico e LLM atrás de feature flags próprias**, cada uma com motivo de deploy documentado e testado (ver seções acima).
- **Contrato de `POST /analyze` estendido de forma aditiva, nunca quebrado**: todos os campos opcionais (semânticos, LLM) usam `response_model_exclude_none=True` — ficam ausentes do JSON (não `null`) quando desligados ou quando o serviço correspondente falha.
- **CI cobre lint, formatação e testes com cobertura, incluindo um Postgres real em container** — não apenas mocks.

---

## API completa

> Cada rota também está disponível na versão prefixada `/api/v1` (ex.: `GET /api/v1/health`), com comportamento idêntico.

### `GET /health`

```json
{ "status": "ok" }
```

### `POST /analyze`

Campos via `multipart/form-data`: `file` (PDF) e `job_description` (string). Header opcional `X-Session-Id` (UUID) — se ausente/inválido, o backend gera um novo automaticamente.

Ver exemplo resumido no README principal. `career_improvement_plan` aparece somente quando há `missing_skills` ou `partial_skills`. Campos opcionais (`semantic_score`, `hybrid_score`, `semantic_matches`, `llm_summary`, `llm_improvement_plan`, `llm_study_suggestions`, `llm_resume_tips`) só aparecem quando as respectivas flags estão ligadas e o serviço responde com sucesso.

### `GET /api/v1/analyses`

> Desligado por padrão (`ENABLE_HISTORY_API=false`) — responde `404` quando desligado. Requer `X-Session-Id` (`422` se ausente/inválido); retorna apenas análises daquela sessão.

Lista análises (mais recentes primeiro), com paginação e filtros (`limit`, `offset`, `min_score`, `skill_status`, `skill_name`). Nunca inclui PDF, texto bruto ou hashes.

### `GET /api/v1/analyses/{analysis_id}`

Detalhe completo de uma análise. `404` se o id não existir, se pertencer a outra sessão (nunca `403`, para não revelar sua existência), ou se a flag estiver desligada.

### `GET /api/v1/analytics/summary`, `/skills`, `/timeline`

> Desligados por padrão (`ENABLE_ANALYTICS_API=false`, flag separada de `ENABLE_HISTORY_API`). Requerem `X-Session-Id`.

Métricas agregadas (total de análises, score médio, ranking de skills, evolução por dia) — nunca um registro individual, PDF, texto bruto ou hash.

---

## Testes e CI

O backend possui 277 testes automatizados com pytest (246 sempre executados + 31 de integração que exigem PostgreSQL — pulados automaticamente sem banco disponível, rodam de fato no CI). Cobertura mínima de 80% imposta via `--cov-fail-under=80`. Testes de matching semântico e feedback via LLM usam exclusivamente mock/stub — nenhum baixa o modelo real nem chama um Ollama real.

O GitHub Actions (`.github/workflows/ci.yml`) roda, em todo push/PR para `main`:
- `backend-tests`: lint (`ruff check .`), format check (`black --check .`), migrations (`alembic upgrade head` contra um Postgres real em container) e os testes com cobertura.
- `frontend-build`: `npm ci` + `npm run build`.

---

## Docker — comandos úteis

```bash
# Derrubar os containers
docker compose down

# Derrubar containers e apagar o volume do PostgreSQL
docker compose down -v

# Ver logs de um serviço
docker compose logs backend
docker compose logs frontend

# Rodar a suíte de testes dentro do container do backend
docker compose exec backend pytest tests/ -v

# Aplicar as migrations do banco (Alembic)
docker compose exec backend alembic upgrade head
```

O setup manual (venv + npm) continua funcionando normalmente — o Docker é uma alternativa, não uma substituição.

---

## Histórico e Dashboard — detalhes

O frontend tem uma aba "Histórico e Dashboard" que consome os endpoints de histórico e analytics. Essa navegação fica sempre visível na interface — inclusive na demo pública — mas os dados só carregam se as feature flags do backend estiverem ligadas. Quando desligadas, a aba exibe "Histórico e analytics estão desativados neste ambiente."

Para ver funcionando localmente, edite o `.env` (não o `.env.example`) antes de `docker compose up --build`:

```bash
ENABLE_HISTORY_API=true
ENABLE_ANALYTICS_API=true
```

Depois, realize 2–3 análises pela aba "Analisar" e acesse "Histórico e Dashboard" para ver os cards de resumo, o ranking de skills, a evolução de score e a lista paginada de análises.

---

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` libera CORS para qualquer origem; qualquer outro valor restringe ao `FRONTEND_ORIGIN`. |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Origem aceita pelo CORS em produção. |
| `DATABASE_URL` | — | String de conexão PostgreSQL, usada por SQLAlchemy/Alembic. |
| `ENABLE_HISTORY_API` | `false` | Liga os endpoints de leitura do histórico. |
| `ENABLE_ANALYTICS_API` | `false` | Liga os endpoints de analytics agregada. |
| `ENABLE_SEMANTIC_MATCHING` | `false` | Liga o enriquecimento semântico via embeddings. |
| `ENABLE_LLM_FEEDBACK` | `false` | Liga o feedback textual via LLM local. |
| `LLM_PROVIDER` | `ollama` | Provider de LLM ativo (só Ollama implementado). |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL do Ollama local. |
| `OLLAMA_MODEL` | `llama3.1` | Modelo a usar via Ollama. |
| `VITE_API_BASE_URL` | — | URL do backend usada pelo frontend (Vite). |

Todas as feature flags aceitam `"true"/"1"/"yes"` (case-insensitive); qualquer outro valor é tratado como `false`.
