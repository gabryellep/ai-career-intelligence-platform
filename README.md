# AI Career Intelligence Platform

> Evoluído a partir do **AI Resume Analyzer** — plataforma de análise de compatibilidade entre currículo e vaga, com score explicável, identificação de gaps técnicos e recomendações práticas de melhoria.

Este projeto nasceu como **AI Resume Analyzer**, um analisador de currículos com motor determinístico. Evoluiu para **AI Career Intelligence Platform**: uma plataforma mais completa, com histórico de análises, dashboard, matching semântico via embeddings e feedback textual via LLM local — todas essas camadas mais avançadas implementadas, testadas e **desligadas por padrão em produção** (ver [Local-only features](#local-only-features)), mantendo o mesmo compromisso com um motor determinístico explicável como fonte de verdade. O nome técnico do repositório (`ai-resume-analyzer`) permanece o mesmo; o reposicionamento é de produto, não de código.

---

## Demo

- **Frontend:** https://ai-resume-analyzer-app-pi.vercel.app
- **Backend/API:** https://ai-resume-analyzer-wh05.onrender.com
- **Documentação da API (Swagger):** https://ai-resume-analyzer-wh05.onrender.com/docs

> Observação: o backend está hospedado em plano gratuito no Render. Em alguns acessos, a primeira requisição pode demorar alguns segundos porque o serviço pode "acordar" após um período de inatividade.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)
[![CI](https://github.com/gabryellep/ai-resume-analyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/gabryellep/ai-resume-analyzer/actions/workflows/ci.yml)
![Deploy](https://img.shields.io/badge/Deploy-Render%20%2B%20Vercel-purple?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Visão geral

Candidatos costumam se candidatar a vagas sem saber, de forma objetiva, o quanto o próprio currículo atende aos requisitos pedidos — nem quais gaps priorizar antes de enviar a candidatura.

O **AI Career Intelligence Platform** resolve isso comparando um currículo em PDF com a descrição de uma vaga e devolvendo, em segundos, um score de compatibilidade explicável, a lista de skills atendidas/faltantes/parciais/extras, pontos fortes, pontos de atenção e recomendações práticas de melhoria.

**Escopo**: a ferramenta foi projetada e testada para vagas de **tecnologia, IA/dados e engenharia de software** — o dicionário de skills (linguagens, frameworks, cloud, bancos de dados, MLOps etc.) e as recomendações refletem esse domínio. Para vagas fora da área tech, os resultados tendem a ser menos precisos ou pouco úteis, já que o motor não reconhece skills e termos de outras áreas.

A versão atual usa um **motor determinístico, explicável e testável** — não uma IA generativa. Cada resultado pode ser auditado: é possível apontar exatamente por que o score deu 38 e não 70. Essa decisão é intencional e está detalhada na seção [Decisões técnicas](#decisões-técnicas).

---

## Problema

- Candidatos não sabem objetivamente o quanto seu currículo atende a uma vaga específica.
- Não fica claro quais gaps técnicos priorizar antes de se candidatar.
- Currículos e vagas usam termos diferentes para a mesma tecnologia (ex.: "Postgres" vs. "PostgreSQL"), gerando comparações injustas quando feitas manualmente.
- Feedback de recrutadores, quando existe, raramente é estruturado ou acionável.

## Solução

O sistema extrai o texto do currículo, identifica skills técnicas e idiomas (com aliases e sinônimos), compara com os requisitos da vaga e gera:

- score de compatibilidade (0–100), calculado de forma ponderada e explicável;
- skills encontradas, faltantes, parcialmente atendidas e extras;
- pontos fortes, pontos de atenção e próximos passos;
- recomendações práticas e acionáveis para melhorar o currículo antes da candidatura.

O **score determinístico nunca usa LLM, embedding ou modelo de machine learning** — é regra determinística, auditável e coberta por testes automatizados. Camadas opcionais de embeddings e LLM existem no projeto (ver seções próprias abaixo) e podem enriquecer a resposta com campos adicionais quando ligadas localmente, mas nunca substituem nem influenciam o score determinístico, e ficam **desligadas por padrão em produção**. Ver [Motor determinístico e explicável](#motor-determinístico-e-explicável).

Como o currículo pode conter dados pessoais, o upload é validado no backend (extensão, tipo MIME, assinatura binária do arquivo e limite de tamanho) e o envio exige consentimento explícito no frontend. O arquivo é processado apenas em memória, durante a própria requisição, sem ser salvo em disco ou persistido — ver [PRIVACY.md](PRIVACY.md) para o detalhamento completo.

---

## Demo flow

Como demonstrar o projeto em poucos minutos:

1. Suba o ambiente completo com Docker Compose (`cp .env.example .env && docker compose up --build`) ou acesse a demo pública (ver [Demo](#demo) acima).
2. Abra o frontend (`http://localhost:5173` local, ou o link da Vercel na demo pública).
3. Faça upload de um currículo em PDF de exemplo e cole uma descrição de vaga.
4. Veja o score de compatibilidade, as skills atendidas/faltantes/parciais/extras, os insights e as recomendações — tudo calculado pelo motor determinístico, em segundos.
5. **Opcional, apenas local** (não faz parte da demo pública — ver [Local-only features](#local-only-features)):
   - ligue `ENABLE_HISTORY_API=true` e `ENABLE_ANALYTICS_API=true` para ver a aba "Histórico e Dashboard" com dados reais na **interface** (ver [Histórico e Dashboard](#histórico-e-dashboard-opcional-apenas-local));
   - ligue `ENABLE_SEMANTIC_MATCHING=true` (exige `pip install -r requirements-dev.txt`) para ver `semantic_score`/`hybrid_score`/`semantic_matches` **no JSON de resposta** de `POST /analyze` — inspecione via `/docs` (Swagger), `curl` ou o painel de rede (DevTools) do navegador; **o frontend não exibe esses campos na tela** (ver [Matching semântico com embeddings](#matching-semântico-com-embeddings-opcional-spec-0011));
   - instale o Ollama e ligue `ENABLE_LLM_FEEDBACK=true` para ver `llm_summary` e as demais sugestões **no JSON de resposta**, pelo mesmo caminho (`/docs`, `curl` ou DevTools) — **também não aparece na interface** (ver [Feedback textual via LLM local](#feedback-textual-via-llm-local-opcional-spec-0014)).

---

## Architecture highlights

- **Camadas desacopladas**: `app/api` (rotas HTTP) → `app/services` (orquestração) → `app/engines` (motor determinístico + motor semântico opcional) → `app/repositories` (persistência). O motor determinístico, por exemplo, não conhece banco de dados nem HTTP.
- **Feature flags como padrão consistente**: 4 capacidades opcionais (histórico, analytics, matching semântico, feedback via LLM) seguem exatamente o mesmo padrão — desligadas por padrão, testadas com a flag ligada em CI/local, com fallback silencioso testado caso a capacidade falhe.
- **Migrations aditivas, nunca destrutivas**: as 4 migrations do projeto (SPECs 0004/0009/0011/0014) adicionam colunas nullable sem quebrar dados existentes.
- **Testes de integração contra PostgreSQL real, não apenas mocks**: a suíte roda contra um Postgres de verdade (container no CI; `pgserver` em verificações manuais locais) — não apenas contra um banco simulado.
- **API versionada sem duplicar lógica**: rotas legadas (`/analyze`) e versionadas (`/api/v1/analyze`) compartilham a mesma implementação.
- **Resiliência por padrão**: falha de banco, falha de embeddings ou falha de LLM nunca quebram `POST /analyze` — o fluxo central sempre responde.

## AI Engineering highlights

- **Motor determinístico como baseline deliberado**: antes de adicionar qualquer modelo de ML, o projeto implementou e testou um motor 100% explicável (regras, aliases, matching ponderado) — evita usar IA sem necessidade comprovada.
- **Matching semântico com embeddings reais, não hipotético**: `sentence-transformers`/`all-MiniLM-L6-v2` rodando localmente, com scripts de validação (`semantic_demo.py`) e calibração (`semantic_calibration.py`) que geram métricas reais sobre pares de skills rotulados.
- **Calibração orientada a dados, não a intuição**: o threshold de similaridade foi ajustado de `0.70` para `0.50` com base em precision/recall/F1 medidos sobre 44 pares rotulados (27 positivos + 17 negativos) — ver [Calibração do matching semântico](#calibração-do-matching-semântico-spec-0013).
- **Integração com LLM local (Ollama), com validação estrita de saída**: o feedback textual gerado pelo modelo passa por um schema de validação antes de ser aceito — resposta fora do formato esperado é descartada, nunca exposta parcialmente.
- **IA como camada aditiva, nunca como fonte de verdade**: embeddings e LLM só enriquecem o resultado com campos extras opcionais — o score determinístico nunca é alterado por nenhum dos dois.
- **Decisões de deploy fundamentadas em custo real**, não em suposição: cada capacidade de IA opcional documenta explicitamente seu custo de infraestrutura antes de sequer ser considerada para produção — ver [Local-only features](#local-only-features).

## Software Engineering highlights

- Arquitetura em camadas (API / serviços / motores / repositórios), com responsabilidades bem delimitadas.
- Suíte de testes automatizados (pytest) com cobertura mínima de 80% imposta no CI (`--cov-fail-under=80`), incluindo testes de integração contra PostgreSQL real — ver [Testes](#testes) para os números atuais.
- Migrations versionadas (Alembic), todas aditivas — nenhuma até hoje exigiu downtime ou backfill complexo.
- Pipeline de CI (GitHub Actions) validando lint (Ruff), formatação (Black) e testes a cada push/PR.
- Feature flags com fallback testado — cada capacidade opcional tem testes cobrindo o caminho de sucesso e o de falha.
- Decisões técnicas documentadas e datadas por Spec (ver [Decisões técnicas](#decisões-técnicas)) — rastreabilidade de por que cada escolha foi feita.
- Privacidade tratada como requisito de design desde o início (hashes em vez de dados brutos) — não como correção posterior.
- Containerização (Docker/Docker Compose) e deploy real e público (Render + Vercel).

## Security & Privacy

Resumo — detalhamento completo em [PRIVACY.md](PRIVACY.md):

- O PDF, o texto do currículo e o texto da vaga **nunca são persistidos** — apenas hashes SHA-256, metadados e o resultado estruturado da análise.
- Upload validado (extensão, MIME, assinatura binária do arquivo, tamanho máximo) antes de qualquer processamento.
- Isolamento por sessão anônima (`X-Session-Id`) desde a SPEC 0009 — **não é autenticação real**: quem souber o UUID de uma sessão consegue ler os dados daquela sessão. Trate como conveniência de portfólio, não como proteção contra um atacante determinado.
- CORS restrito a `FRONTEND_ORIGIN` em produção (`ENVIRONMENT=production`) — aberto apenas em desenvolvimento local.
- Quando o feedback via LLM está ligado (só localmente), apenas dados já estruturados (score, skills, insights) são enviados ao modelo — nunca PDF, texto bruto, hashes ou `session_id`; o prompt completo e a resposta bruta do modelo nunca são persistidos.
- Sem rate limiting e sem autenticação de usuário nesta versão — ver [Limitações atuais](#limitações-atuais) e [docs/deploy-checklist.md](docs/deploy-checklist.md) para as pendências antes de produção plena.

## Local-only features

| Feature | Flag | Por que está desligada em produção | Como testar localmente |
|---|---|---|---|
| Histórico de análises | `ENABLE_HISTORY_API=false` | Falta autenticação real — o isolamento por `X-Session-Id` não é forte o suficiente para expor histórico individual publicamente. | Ligar a flag no `.env` local + Docker Compose (ver [Histórico e Dashboard](#histórico-e-dashboard-opcional-apenas-local)). |
| Analytics agregada | `ENABLE_ANALYTICS_API=false` | Mesmo motivo do histórico — mesmo expondo só números agregados, o perfil de risco justifica a mesma cautela. | Idem, `ENABLE_ANALYTICS_API=true`. |
| Matching semântico (embeddings) | `ENABLE_SEMANTIC_MATCHING=false` | Peso de deploy: `sentence-transformers`/`torch` (centenas de MB) não cabem no plano gratuito do Render atual. | `pip install -r requirements-dev.txt` + `ENABLE_SEMANTIC_MATCHING=true` (ver [Matching semântico com embeddings](#matching-semântico-com-embeddings-opcional-spec-0011)). |
| Feedback via LLM local | `ENABLE_LLM_FEEDBACK=false` | Ollama é um processo externo que não existe no ambiente de deploy atual (sem GPU, sem processo de longa duração). | Instalar Ollama + `ollama pull llama3.1` + `ENABLE_LLM_FEEDBACK=true` (ver [Feedback textual via LLM local](#feedback-textual-via-llm-local-opcional-spec-0014)). |

Nenhuma dessas quatro flags está ligada na demo pública (Render/Vercel) — todas existem, têm testes automatizados e documentação completa, mas foram deliberadamente mantidas desligadas em produção por razões específicas e documentadas (autenticação, peso de deploy, ou dependência de processo externo), não por estarem incompletas.

---

## Funcionalidades

O que já está implementado e funcionando na versão atual:

- Upload de currículo em PDF;
- Leitura automática do conteúdo do PDF;
- Campo para colar a descrição da vaga;
- Extração de skills técnicas com regex e dicionário com mais de 100 termos;
- Suporte a aliases e sinônimos (ex.: "K8s" → "Kubernetes");
- Detecção de idioma com níveis (básico/intermediário/avançado);
- Score de compatibilidade de 0 a 100, ponderado e explicável;
- Classificação de skills em atendidas, faltantes, parcialmente atendidas e extras;
- Recomendações práticas baseadas nos gaps encontrados;
- Seção de insights do perfil (pontos fortes, pontos de atenção, próximos passos);
- Interface web responsiva;
- API REST com FastAPI e documentação automática via Swagger;
- 243 testes automatizados com pytest cobrindo parser, skills, matcher, score, recomendações, rotas da API, persistência, histórico, analytics, isolamento por sessão, matching semântico e feedback via LLM (ver [Testes](#testes) para o detalhamento);
- Execução local via Docker/Docker Compose (backend, frontend e PostgreSQL);
- Persistência do resultado de cada análise (score, skills, insights, recomendações) em PostgreSQL via SQLAlchemy/Alembic — nunca o PDF ou o texto bruto do currículo/vaga (ver [PRIVACY.md](PRIVACY.md));
- Frontend de Histórico e Dashboard (aba própria) consumindo os endpoints de histórico e analytics — funcional **localmente** quando as feature flags do backend estão ligadas (ver [Histórico e Dashboard](#histórico-e-dashboard-opcional-apenas-local));
- Matching semântico opcional via embeddings, calibrado empiricamente — funcional **localmente/CI** (ver [Matching semântico com embeddings](#matching-semântico-com-embeddings-opcional-spec-0011));
- Feedback textual opcional via LLM local (Ollama) — funcional **localmente**, nunca decide score ou matching (ver [Feedback textual via LLM local](#feedback-textual-via-llm-local-opcional-spec-0014));
- Pipeline de CI (GitHub Actions) validando lint, formatação, testes com cobertura (backend, incluindo um Postgres de teste) e build do frontend em todo push/PR.

Todas as funcionalidades acima **existem e são testadas** — o que muda de uma para outra é se estão ativas na demo pública (ver [Local-only features](#local-only-features)) ou apenas em ambiente local/dev. O que ainda não foi implementado está listado no [Roadmap](#roadmap).

---

## Screenshots

<!-- As imagens abaixo ainda não existem neste repositório. -->
<!-- Assim que forem capturadas (sempre com dados sintéticos, nunca um currículo real — -->
<!-- ver docs/images/README.md), adicione os arquivos em docs/images/ com estes nomes exatos: -->
<!-- docs/images/home.png, docs/images/result.png, docs/images/dashboard.png, -->
<!-- docs/images/analytics.png, docs/images/llm-feedback.png, docs/images/architecture.png, -->
<!-- docs/images/demo.gif -->

*(Screenshots e GIF de demonstração ainda não foram capturados — a estrutura de pastas e o checklist completo já estão preparados em [`docs/images/README.md`](docs/images/README.md). Ver a seção [API](#api) abaixo para um exemplo real de resposta JSON sem depender de imagens.)*

| Print | Conteúdo esperado | Status |
|---|---|---|
| `home.png` | Tela inicial (upload de currículo + descrição da vaga) | Pendente |
| `result.png` | Tela de resultado (score, skills, insights, recomendações) | Pendente |
| `dashboard.png` | Aba Histórico e Dashboard, com dados sintéticos (ver [Histórico e Dashboard](#histórico-e-dashboard-opcional-apenas-local)) | Pendente |
| `analytics.png` | Cards de analytics agregada (score médio, skills mais faltantes) | Pendente |
| `llm-feedback.png` | Resposta com `llm_summary`/`llm_improvement_plan` visível (Ollama local ligado) | Pendente |
| `architecture.png` | Diagrama de arquitetura em imagem (complementar ao Mermaid abaixo) | Pendente |
| `demo.gif` | Fluxo completo: upload → análise → resultado (30–60s) | Pendente |

---

## Arquitetura

O projeto é dividido em duas partes principais: backend (FastAPI) e frontend (React/Vite), comunicando-se via API REST.

```mermaid
flowchart LR
  UI[React + Vite] --> API[FastAPI]
  API --> Engine[Analysis Engine]
  Engine --> Parser[Parser - PyMuPDF]
  Engine --> Matcher[Matcher]
  Engine --> Recommender[Recommender]
```

Estrutura de pastas:

```text
ai-resume-analyzer/
│
├── backend/
│   ├── main.py                         # bootstrap do FastAPI, CORS, registro de rotas
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── api/v1/                     # rotas HTTP (/health, /analyze) e router versionado
│   │   ├── core/                       # configuração (config.py) e erros HTTP (exceptions.py)
│   │   ├── domain/schemas/             # contratos Pydantic de request/response
│   │   ├── services/                   # AnalysisService, PdfValidationService
│   │   └── engines/deterministic/      # parser, skills, matcher, scorer, recommender, analyzer
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
├── docker-compose.yml
└── .github/workflows/ci.yml
```

O backend é organizado em camadas: as rotas (`app/api/v1`) apenas coordenam a requisição HTTP, delegando validação de upload ao `PdfValidationService` e orquestração da análise ao `AnalysisService`, que por sua vez chama o motor determinístico em `app/engines/deterministic`. As rotas `GET /health`/`POST /analyze` (legadas) e `GET /api/v1/health`/`POST /api/v1/analyze` (versionadas) compartilham exatamente a mesma implementação — não há lógica duplicada entre elas. O frontend é responsável por receber o PDF e a descrição da vaga, enviar os dados para a API e exibir o resultado de forma visual e organizada.

---

## Como a análise funciona

```mermaid
flowchart LR
  A[Upload PDF + descricao da vaga] --> B[Extracao de texto - PyMuPDF]
  B --> C[Extracao de skills - regex + dicionario]
  C --> D[Normalizacao e aliases]
  D --> E[Matching deterministico ponderado]
  E --> F[Score explicavel]
  F --> G[Insights]
  G --> H[Recomendacoes]
  H --> I[Frontend React]
```

### Extração de skills

O sistema utiliza um dicionário de skills técnicas e padrões com regex para identificar termos relevantes no currículo e na vaga. Exemplos: Python, JavaScript, TypeScript, FastAPI, React, Docker, Kubernetes, AWS, PostgreSQL, Pandas, Machine Learning, GitHub Actions, CI/CD, níveis de inglês.

### Aliases e sinônimos

Para reduzir falsos negativos, termos equivalentes são tratados como a mesma skill:

| Termo encontrado | Skill canônica |
|---|---|
| Amazon Web Services | AWS |
| Postgres / Postgres SQL | PostgreSQL |
| NodeJS | Node.js |
| JS | JavaScript |
| TS | TypeScript |
| CI CD | CI/CD |
| Machine-learning | Machine Learning |
| K8s | Kubernetes |
| Sklearn | Scikit-learn |

### Detecção de idiomas

O sistema diferencia níveis de inglês, evitando que qualquer menção a "inglês" seja tratada como nível avançado:

| Texto encontrado | Interpretação |
|---|---|
| inglês / english | english_basic |
| inglês intermediário / intermediate english / B1 / B2 | english_intermediate |
| inglês avançado / advanced english / fluent english / C1 / C2 | english_advanced |

Exemplo:

```text
Vaga: Python, Docker e inglês avançado C1
Currículo: Python e inglês intermediário B2

Resultado:
Python → atendido
Docker → ausente
Inglês avançado → parcialmente atendido
```

### Matching avançado

As skills são classificadas em quatro grupos:

- **Encontradas**: exigidas pela vaga e presentes no currículo.
- **Faltantes**: exigidas pela vaga, mas ausentes no currículo.
- **Parcialmente atendidas**: presentes no currículo, mas não no nível exigido (ex.: inglês avançado exigido, intermediário encontrado).
- **Extras**: presentes no currículo, mas não exigidas na vaga — podem ser diferenciais em outras oportunidades.

### Cálculo do score

O score é calculado de forma ponderada e explicável:

```text
Skill atendida completamente = 1.0 ponto
Skill parcialmente atendida = 0.5 ponto
Skill ausente = 0 ponto

score = round(pontos_obtidos / total_de_skills_exigidas * 100)
```

Exemplo:

```text
Vaga: Python, Docker, AWS, inglês avançado
Currículo: Python, inglês intermediário

Python = 1.0
Inglês avançado = 0.5
Docker = 0
AWS = 0

score = round(1.5 / 4 * 100) = 38
```

Essa abordagem é mais justa do que um simples "tem ou não tem".

### Recomendações e insights

As recomendações são geradas com base nas skills faltantes, parcialmente atendidas e no score geral — por exemplo, sugerir um projeto prático com a tecnologia ausente, ou orientar a informar o nível de inglês no padrão CEFR. A seção de insights do perfil resume pontos fortes (ex.: boa cobertura em linguagens de programação), pontos de atenção (ex.: gaps em cloud/DevOps) e próximos passos priorizados.

---

## Motor determinístico e explicável

A versão atual **não utiliza IA generativa**. A decisão técnica foi priorizar um motor de análise determinístico, explicável e testável, baseado em extração de texto de PDF, regex, dicionário de skills, aliases, matching ponderado e regras para níveis de inglês.

Isso significa que:

- o score pode ser explicado passo a passo;
- os 243 testes automatizados (212 sempre executados + 31 de integração com Postgres) validam a lógica de ponta a ponta;
- o sistema não depende de APIs pagas de terceiros;
- os resultados são previsíveis e reprodutíveis;
- a análise pode ser auditada e melhorada com regras claras, sem efeitos colaterais de um modelo de linguagem.

Desde a SPEC 0011, existe também uma camada opcional de matching semântico via embeddings (`sentence-transformers`), desligada por padrão — ver seção própria abaixo. Uma camada de LLM para feedback textual continua planejada como evolução futura — não para substituir o score determinístico, mas para complementá-lo. Ver [Roadmap](#roadmap).

---

## Matching semântico com embeddings (opcional, SPEC 0011)

O motor determinístico (acima) não entende sinônimos que não estejam cadastrados em seu dicionário de aliases — por exemplo, "ML engineer" no currículo não bate com "machine learning" exigido pela vaga, a menos que ambos já estejam mapeados. Desde a SPEC 0011, existe uma camada opcional que usa embeddings para aproximar esses casos, **sem substituir nem alterar** o motor determinístico.

**Como funciona, quando ligada:**
- Modelo: [`sentence-transformers`](https://www.sbert.net/) com `all-MiniLM-L6-v2` — leve para o padrão da família (≈90 MB de pesos), roda em CPU, sem necessidade de GPU.
- Embeddings são calculados **apenas sobre nomes de skills** (ex.: `"docker"`, `"machine learning"`) — nunca sobre o texto do currículo ou da vaga.
- Só entra em ação para skills que o determinístico já classificou como `missing`: para cada uma, procura a skill `extra` do currículo com maior similaridade de cosseno; acima do threshold (`0.50`, calibrado empiricamente na SPEC 0013 — ver seção própria abaixo), conta como aproximação semântica.
- `semantic_score`: mesma fórmula de peso do score determinístico (matched=1.0, partial=0.5), tratando cada aproximação semântica como um "partial" adicional (peso 0.5).
- `hybrid_score`: `70% score determinístico + 30% semantic_score`.
- `semantic_matches`: lista (máx. 10 itens, ordenada por similaridade decrescente) mostrando exatamente qual skill da vaga foi aproximada de qual skill do currículo, e com que similaridade — preserva a explicabilidade, nunca uma "caixa preta".

**Desligada por padrão, inclusive em produção** (`ENABLE_SEMANTIC_MATCHING=false`): a dependência (`sentence-transformers`, que traz `torch` transitivamente — centenas de MB) fica só em `requirements-dev.txt`, nunca na imagem Docker de produção (ver `Dockerfile`, que instala apenas `requirements.txt`). Ligar a flag em produção sem essa dependência instalada não quebra nada — o fallback (ver abaixo) garante que a análise responde normalmente, só sem o enriquecimento semântico. A justificativa de peso é a mesma já usada para as flags de histórico/analytics (ver [docs/deploy-checklist.md](docs/deploy-checklist.md)): o plano gratuito do Render não comporta a RAM adicional para carregar o modelo.

**Fallback em 3 camadas** — `POST /analyze` nunca quebra por causa desta camada:
1. flag desligada → o código nem tenta importar a dependência;
2. dependência ausente (caso de produção) → erro de import contido, campos semânticos ausentes;
3. falha em tempo de execução (modelo indisponível, erro de inferência) → mesmo comportamento do item 2.

**Contrato de `POST /analyze`**: `semantic_score`, `hybrid_score` e `semantic_matches` são campos **opcionais e aditivos** — com a flag desligada (padrão), a resposta é byte-a-byte idêntica à anterior a esta Spec (`response_model_exclude_none=True` garante que os campos ausentes não aparecem como `null` no JSON). O `score` determinístico nunca muda.

### Validação local do matching semântico (SPEC 0012)

Os números acima descrevem *como a camada funciona*; esta seção registra o que o **modelo real** (`all-MiniLM-L6-v2`), rodado localmente, de fato produziu — sem maquiar resultado ruim. Reproduza com `python backend/scripts/semantic_demo.py` (exige `pip install -r requirements-dev.txt`; baixa os pesos do modelo na primeira execução; não roda no CI nem afeta o deploy).

Resultado observado sobre os pares de skills testados (threshold `0.70`):

| Skill da vaga | Skill do currículo | Similaridade real | Passou do threshold? |
|---|---|---|---|
| docker | containers | 0.60 | não |
| postgresql | relational database | 0.49 | não |
| nlp | text processing | 0.49 | não |
| python | excel | 0.39 | — (falso positivo esperado, corretamente rejeitado) |
| fastapi | python api | 0.27 | não |
| react | frontend | 0.25 | não |
| docker | ux design | 0.23 | — (falso positivo esperado, corretamente rejeitado) |
| ci/cd | github actions | 0.12 | não |
| react | postgresql | 0.01 | — (falso positivo esperado, corretamente rejeitado) |

**Achado honesto**: com o threshold atual (`0.70`), **nenhum** dos 6 pares de aproximação semântica esperada foi de fato capturado — o mais próximo foi `docker ↔ containers` em `0.60`. Em compensação, os 3 pares de falso positivo testados ficaram corretamente baixos (`0.01`–`0.39`), então a camada não está gerando aproximações indevidas — está apenas conservadora demais para o formato de comparação usada (nomes curtos de skills, sem frase/contexto). Isso é consistente com o comportamento conhecido de modelos `sentence-transformers`: eles tendem a pontuar mais alto frases completas e comparáveis do que substantivos técnicos isolados.

No cenário de antes/depois testado (vaga: `python, docker, postgresql, ci/cd, aws`; currículo: `python, containers, relational database, github actions`), nenhum par cruzou o threshold, então `semantic_score` e `hybrid_score` ficaram idênticos ao `score` determinístico (`20`) — o pior caso possível para a camada semântica, mas o esperado dado o resultado acima.

**Conclusão desta Spec**: o threshold `0.70` e os pesos `70%/30%` **não foram alterados** (fora do escopo da SPEC 0012) — a evidência aponta que valeria a pena revisar o threshold (algo entre `0.55` e `0.60` teria capturado `docker ↔ containers` sem admitir nenhum dos falsos positivos testados), mas essa calibração fica para uma Spec futura dedicada a isso, com mais pares de validação antes de mudar um valor que afeta produção. **Atualização (SPEC 0013)**: essa calibração foi feita — ver seção abaixo. O threshold mudou de `0.70` para `0.50`.

### Calibração do matching semântico (SPEC 0013)

A SPEC 0012 (acima) levantou a hipótese, com apenas 9 pares, de que reduzir o threshold poderia melhorar o recall sem introduzir falsos positivos. A SPEC 0013 testou essa hipótese com uma amostra bem maior — **27 pares positivos e 17 pares negativos** (incluindo "armadilhas" propositais como `java ↔ javascript` e `c ↔ c#`, tecnologias com nomes parecidos mas sem relação real) — contra 5 thresholds candidatos. Reproduza com `python backend/scripts/semantic_calibration.py` (mesmos pré-requisitos do script da SPEC 0012; gera `backend/scripts/semantic_calibration_output.md` com a tabela completa de pares).

| Threshold | TP | FN | FP | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.50 | 9 | 18 | 0 | 17 | 1.00 | 0.33 | **0.50** |
| 0.55 | 8 | 19 | 0 | 17 | 1.00 | 0.30 | 0.46 |
| 0.60 | 3 | 24 | 0 | 17 | 1.00 | 0.11 | 0.20 |
| 0.65 | 2 | 25 | 0 | 17 | 1.00 | 0.07 | 0.14 |
| 0.70 (valor anterior) | 2 | 25 | 0 | 17 | 1.00 | 0.07 | 0.14 |

**Decisão: threshold reduzido de `0.70` para `0.50`** (`app/engines/semantic/hybrid.py::SEMANTIC_SIMILARITY_THRESHOLD`). Justificativa pelos números acima: **nos 17 pares negativos testados, o maior valor observado foi `java ↔ javascript` em `0.40`** — ou seja, mesmo no threshold candidato mais baixo (`0.50`), sobra uma margem de `0.10` antes de admitir qualquer falso positivo da amostra. Reduzir o threshold não custou nenhuma precisão (permaneceu `1.00` em todos os candidatos testados) e dobrou o recall (`0.07 → 0.33`) e o F1 (`0.14 → 0.50`) — o melhor resultado entre os 5 candidatos avaliados.

Exemplos que passam a ser capturados com `0.50` (antes ficavam de fora): `rest api ↔ http api` (0.76), `linux ↔ unix operating system` (0.76), `mongodb ↔ nosql database` (0.64), `docker ↔ containers` (0.60), `elasticsearch ↔ search engine` (0.59), `tensorflow ↔ deep learning framework` (0.59), `oauth ↔ authentication protocol` (0.58), `typescript ↔ typed javascript` (0.58), `aws ↔ cloud computing` (0.52), `django ↔ python web framework` (0.50).

**Os pesos do score híbrido continuam `70%/30%`** — nenhuma evidência coletada justificou alterá-los, conforme decisão de escopo desta Spec.

**Isso não muda a decisão de produção**: `ENABLE_SEMANTIC_MATCHING` continua `false` em todo ambiente — calibrar o threshold é uma decisão técnica sobre a qualidade do matching quando a camada estiver ligada; ligá-la em produção depende de outras pendências, não relacionadas ao threshold (ver [docs/deploy-checklist.md](docs/deploy-checklist.md)): peso de deploy (`sentence-transformers`/`torch`) e, mais amplamente, as mesmas questões de autenticação/rate limiting que mantêm histórico e analytics desligados.

**Limitação reconhecida**: com apenas 27+17 pares, esta continua sendo "a melhor evidência disponível hoje", não uma calibração estatisticamente definitiva — o próprio `0.50` foi o *menor* threshold testado (não foram avaliados valores abaixo dele), então é possível que um valor ainda menor tivesse F1 melhor; isso fica para uma futura calibração, se e quando a camada for considerada para produção.

---

## Feedback textual via LLM local (opcional, SPEC 0014)

O motor determinístico e o matching semântico (acima) já explicam score, skills e recomendações — mas em formato estruturado. Desde a SPEC 0014, existe uma camada opcional que usa um LLM open-source **rodando localmente via [Ollama](https://ollama.com/)** para reescrever esse resultado em linguagem mais natural. **O LLM nunca decide nada** — só lê o resultado já calculado (score, skills, insights) e gera texto explicativo a partir dele; `score`, `matched_skills`, `missing_skills`, `match_details` e os campos semânticos continuam sendo calculados exclusivamente pelo motor determinístico/semântico, sem nenhuma influência do LLM.

**Como rodar localmente:**

```bash
# 1. Instalar o Ollama: https://ollama.com/download
# 2. Baixar o modelo padrão
ollama pull llama3.1

# 3. No seu .env (backend), ligar a flag
ENABLE_LLM_FEEDBACK=true
OLLAMA_MODEL=llama3.1          # opcional, já é o padrão
OLLAMA_BASE_URL=http://localhost:11434   # opcional, já é o padrão

# 4. Rodar o backend normalmente e chamar POST /analyze — a resposta passa
#    a incluir llm_summary, llm_improvement_plan, llm_study_suggestions e
#    llm_resume_tips.
```

**O que é enviado ao LLM (e o que nunca é)**: apenas dados já estruturados — `score`, `matched_skills`, `missing_skills`, `partial_skills`, `extra_skills`, `insights` e, se existirem, `semantic_score`/`hybrid_score`. **Nunca** o PDF, o texto do currículo/vaga, hashes ou `session_id`. Ver [PRIVACY.md](PRIVACY.md) para o detalhamento completo.

**Campos gerados** (opcionais e aditivos, mesma regra de ausência do `semantic_score` — ver seção acima): `llm_summary` (parágrafo curto), `llm_improvement_plan`, `llm_study_suggestions`, `llm_resume_tips` (até 5 itens cada).

**Fallback**: se `ENABLE_LLM_FEEDBACK` estiver desligada (padrão), se o Ollama não estiver rodando/acessível, se a chamada estourar o timeout (20s) ou se a resposta não vier em JSON válido no formato esperado, `POST /analyze` responde normalmente, apenas sem os campos de LLM — nunca quebra.

**Desligada por padrão, inclusive em produção**: diferente do matching semântico (onde o problema era peso de dependência Python), aqui o motivo é que **Ollama é um processo externo que não existe no ambiente de deploy atual** (Render, sem GPU, sem processo adicional de longa duração). `httpx` (usado para chamar o Ollama) já está em `requirements.txt` de produção — nenhuma dependência nova foi adicionada, mas isso não muda o fato de que não há Ollama para chamar em produção hoje. Ver [docs/deploy-checklist.md](docs/deploy-checklist.md).

**Custo e desempenho**: sem custo de API (o modelo roda inteiramente na sua máquina), mas com custo computacional real — CPU/RAM/energia. Sem GPU, modelos como `llama3.1` podem levar vários segundos para responder; o timeout de 20s prioriza não travar `/analyze`, o que significa que em máquinas mais fracas o feedback pode falhar por timeout com frequência.

**Limitação reconhecida**: não há verificação automática de que o LLM não "alucine" uma skill fora da lista fornecida — a mitigação é só por instrução no prompt (nunca inventar skills, nunca prometer emprego/aprovação), não por validação estrutural. Trate o texto gerado como uma sugestão de redação, não como uma nova fonte de verdade sobre o resultado.

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Extração de PDF | PyMuPDF |
| Validação | Pydantic v2 |
| Frontend | React 18, Vite |
| Estilização | CSS puro |
| Testes | pytest, httpx |
| Containerização | Docker, Docker Compose |
| CI | GitHub Actions |
| Deploy Backend | Render |
| Deploy Frontend | Vercel |

---

## Como rodar com Docker

Sobe backend, frontend e um PostgreSQL local com um único comando, sem precisar instalar Python ou Node na máquina.

> O backend persiste metadados de cada análise no PostgreSQL (score, skills, insights, recomendações, hashes — nunca o PDF ou o texto bruto). Se o banco estiver indisponível, `POST /analyze` continua respondendo normalmente; apenas a persistência é pulada (ver [Decisões técnicas](#decisões-técnicas)).

### Pré-requisitos

- Docker
- Docker Compose (incluso no Docker Desktop)

### Passo a passo

```bash
cp .env.example .env
docker compose up --build
```

### URLs

| Serviço | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| Health check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |

### Comandos úteis

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

O setup manual (venv + npm, descrito abaixo) continua funcionando normalmente — o Docker é uma alternativa, não uma substituição.

---

## Histórico e Dashboard (opcional, apenas local)

O frontend tem uma segunda área, "Histórico e Dashboard" (aba ao lado de "Analisar"), que consome os endpoints de histórico e analytics do backend (`GET /api/v1/analyses`, `GET /api/v1/analytics/summary`, `/skills`, `/timeline`). Essa navegação **fica sempre visível** na interface — inclusive na demo pública — mas os dados só carregam se as feature flags do backend estiverem ligadas.

> **No deploy público, essas flags permanecem desligadas.** Desde a SPEC 0009, o histórico e os analytics já são isolados por sessão anônima (`X-Session-Id`, um UUID salvo no `localStorage` do navegador) — cada sessão só vê os próprios dados — mas isso ainda não é autenticação real (qualquer um com o UUID de uma sessão acessa os dados dela). Ver [PRIVACY.md](PRIVACY.md). Quando as flags estão desligadas, a aba exibe a mensagem "Histórico e analytics estão desativados neste ambiente.", em vez de dados reais.

Para ver o Dashboard funcionando **localmente**, edite o seu `.env` (não o `.env.example`, que continua com as flags em `false`) antes de `docker compose up --build`:

```bash
ENABLE_HISTORY_API=true
ENABLE_ANALYTICS_API=true
```

Depois, realize 2–3 análises pela aba "Analisar" para gerar dados, e acesse a aba "Histórico e Dashboard" em `http://localhost:5173` para ver os cards de resumo, o ranking de skills, a evolução de score e a lista paginada de análises.

**Decisão de deploy (SPEC 0010, revisada em 2026-07-03):** `ENABLE_HISTORY_API` e `ENABLE_ANALYTICS_API` permanecem `false` no deploy público. O isolamento por `X-Session-Id` (SPEC 0009) reduz o risco de um cliente ver dados de outro, mas não é autenticação forte — falta expiração, revogação, rate limiting e autenticação real. O checklist completo de variáveis de ambiente e passos de deploy está em [docs/deploy-checklist.md](docs/deploy-checklist.md).

---

## Como rodar manualmente

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- npm 9+
- Git

### Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend local: `http://127.0.0.1:8000`
Documentação da API: `http://127.0.0.1:8000/docs`

> Rodando o backend manualmente (fora do Docker), é necessário um PostgreSQL acessível e a variável `DATABASE_URL` apontando para ele (ex.: `postgresql://postgres:postgres@localhost:5432/ai_resume_analyzer`), além de aplicar as migrations: `alembic upgrade head`. Sem isso, `POST /analyze` continua funcionando normalmente — apenas a persistência é pulada (ver [Decisões técnicas](#decisões-técnicas)).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend local: `http://localhost:5173`

### Variáveis de ambiente

Em produção, o frontend precisa saber a URL do backend. Na Vercel, foi configurada a variável:

```text
VITE_API_BASE_URL=https://ai-resume-analyzer-wh05.onrender.com
```

Localmente, se essa variável não existir, o frontend usa `/analyze` com o proxy do Vite. No Render, foram configuradas as variáveis:

```text
ENVIRONMENT=production
FRONTEND_ORIGIN=https://ai-resume-analyzer-app-pi.vercel.app
```

---

## Testes

O backend possui 243 testes automatizados com pytest, cobrindo extração de PDF, health check, extração de skills, aliases, níveis de inglês, matching avançado, score ponderado, recomendações, analyzer, rotas da API, persistência, histórico, analytics, isolamento por sessão anônima, matching semântico (mock/stub, sem baixar o modelo real) e feedback via LLM (mock/stub, sem chamar um Ollama real). 31 desses testes exigem um PostgreSQL acessível (via `DATABASE_URL`) e são pulados automaticamente quando não há banco disponível — rodam de fato no CI e em verificações manuais contra um Postgres real.

```bash
cd backend
pytest tests/ -v
```

Build de produção do frontend:

```bash
cd frontend
npm run build
npm run preview   # simula a versão final localmente
```

---

## Integração Contínua (CI)

O projeto usa GitHub Actions (`.github/workflows/ci.yml`) para validar automaticamente todo push e pull request para `main`:

- **`backend-tests`**: instala as dependências de `backend/requirements-dev.txt`, roda lint (`ruff check .`), format check (`black --check .`) e os 243 testes com cobertura (`pytest --cov=app --cov-fail-under=80`).
- **`frontend-build`**: instala as dependências com `npm ci` e executa `npm run build`.

Comandos locais equivalentes (ou use os atalhos do [Makefile](Makefile): `make lint`, `make format-check`, `make test`, `make build-frontend`):

```bash
cd backend
pip install -r requirements-dev.txt
ruff check .
black --check .
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
```

```bash
cd frontend && npm ci && npm run build
```

---

## API

> Cada rota abaixo também está disponível na versão prefixada `/api/v1` (ex.: `GET /api/v1/health`, `POST /api/v1/analyze`), com comportamento idêntico — ambas compartilham a mesma implementação. As rotas sem prefixo são mantidas para compatibilidade com o frontend e a demo atuais.

### `GET /health`

Verifica se a API está funcionando.

```json
{
  "status": "ok"
}
```

### `POST /analyze`

Analisa o currículo com base na descrição da vaga. Campos enviados via `multipart/form-data`:

| Campo | Tipo | Descrição |
|---|---|---|
| file | PDF | Currículo do usuário |
| job_description | string | Descrição da vaga |

Header opcional `X-Session-Id` (UUID) — identifica a sessão anônima do navegador para fins de isolamento de histórico/analytics (ver abaixo). Se ausente ou inválido, o backend gera um novo automaticamente; a análise nunca falha por causa deste header.

Exemplo de resposta:

```json
{
  "score": 33,
  "matched_skills": ["python"],
  "missing_skills": ["docker", "english_advanced"],
  "partial_skills": [],
  "extra_skills": ["go", "machine learning"],
  "match_details": {
    "matched": ["python"],
    "partial": [],
    "missing": ["docker", "english_advanced"],
    "extra": ["go", "machine learning"]
  },
  "insights": {
    "strengths": [
      "Boa cobertura em linguagens de programação: python",
      "Skills diretamente alinhadas com a vaga: python"
    ],
    "weaknesses": [
      "Gap em DevOps e cloud: docker",
      "Compatibilidade baixa — muitos requisitos críticos não atendidos"
    ],
    "priority_actions": [
      "Crie e publique um projeto com Docker no GitHub.",
      "Informe seu nível CEFR de inglês e comprove com certificação.",
      "Priorize as principais skills críticas antes de se candidatar."
    ]
  },
  "recommendations": [
    "A vaga exige docker. Crie um projeto de deploy ou automação usando docker e publique no GitHub com documentação clara.",
    "A vaga exige inglês avançado. Informe seu nível CEFR no currículo e comprove com certificação ou experiência prática.",
    "Seu perfil tem baixa compatibilidade com esta vaga. Priorize os requisitos essenciais antes de se candidatar."
  ]
}
```

Esta é a resposta **padrão e sempre presente**, com todas as flags opcionais desligadas (comportamento da demo pública hoje).

**Exemplo local/dev — com `ENABLE_SEMANTIC_MATCHING=true` e `ENABLE_LLM_FEEDBACK=true`** (não é o comportamento da demo pública; ver [Local-only features](#local-only-features)): a mesma resposta acima ganha campos adicionais, todos opcionais e aditivos — os campos já mostrados acima (`score`, `matched_skills` etc.) permanecem idênticos:

```json
{
  "semantic_score": 45,
  "hybrid_score": 36,
  "semantic_matches": [
    { "job_skill": "docker", "matched_resume_skill": "containers", "similarity": 0.60 }
  ],
  "llm_summary": "Seu perfil atende bem à parte de Python, mas ainda faltam Docker e um nível mais avançado de inglês para esta vaga específica.",
  "llm_improvement_plan": [
    "Priorize um projeto prático com Docker antes de se candidatar novamente.",
    "Informe e comprove seu nível de inglês no padrão CEFR."
  ],
  "llm_study_suggestions": [
    "Curso introdutório de Docker com foco em deploy de aplicações."
  ],
  "llm_resume_tips": [
    "Destaque experiências com Python logo no topo do currículo."
  ]
}
```

> Os valores acima são ilustrativos (gerados manualmente para fins de documentação) — o texto real gerado por um LLM varia a cada execução. Nunca use este bloco como evidência de que embeddings ou LLM rodam na demo pública: ambos ficam desligados em produção (ver [Local-only features](#local-only-features)).

### `GET /api/v1/analyses`

> Desligado por padrão. Controlado pela variável `ENABLE_HISTORY_API` (`false` por padrão) — quando desligado, este endpoint (e o de detalhe abaixo) responde `404`, como se não existisse. Existe apenas sob `/api/v1` (sem equivalente sem prefixo). **Requer o header `X-Session-Id` (UUID)** — `422` se ausente ou inválido; retorna apenas análises daquela sessão (ver [PRIVACY.md § Isolamento por sessão anônima](PRIVACY.md#isolamento-por-sessão-anônima-desde-a-spec-0009)). Ver [Decisões técnicas](#decisões-técnicas) e [PRIVACY.md](PRIVACY.md) para o porquê.

Lista análises já persistidas (mais recentes primeiro), com paginação e filtros opcionais.

| Query param | Tipo | Descrição |
|---|---|---|
| limit | int | Itens por página (padrão 20, máx. 100) |
| offset | int | Itens a pular (padrão 0) |
| min_score | int | Score mínimo (inclusive) |
| skill_status | string | `matched`, `partial`, `missing` ou `extra` |
| skill_name | string | Nome de uma skill (ex.: `docker`) |

Exemplo de resposta:

```json
{
  "items": [
    {
      "id": "b7e1c2b0-3f2a-4e9a-9b8a-2e0f6a1c9d4e",
      "score": 80,
      "matched_skills": ["docker", "python"],
      "missing_skills": ["aws"],
      "partial_skills": [],
      "extra_skills": [],
      "created_at": "2026-07-03T18:22:41.123456Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Nunca inclui PDF, texto bruto de currículo/vaga, ou hashes.

### `GET /api/v1/analyses/{analysis_id}`

Detalhe completo de uma análise. `404` se o `id` não existir, se pertencer a outra sessão (nunca `403`, para não revelar sua existência), ou se `ENABLE_HISTORY_API=false`; `422` se `analysis_id` ou `X-Session-Id` não forem UUIDs válidos.

```json
{
  "id": "b7e1c2b0-3f2a-4e9a-9b8a-2e0f6a1c9d4e",
  "score": 80,
  "matched_skills": ["docker", "python"],
  "missing_skills": ["aws"],
  "partial_skills": [],
  "extra_skills": [],
  "created_at": "2026-07-03T18:22:41.123456Z",
  "match_details": { "matched": ["docker", "python"], "partial": [], "missing": ["aws"], "extra": [] },
  "insights": { "strengths": ["..."], "weaknesses": ["..."], "priority_actions": ["..."] },
  "recommendations": ["..."]
}
```

### `GET /api/v1/analytics/summary`

> Desligado por padrão. Controlado por `ENABLE_ANALYTICS_API` (`false` por padrão, **separada** de `ENABLE_HISTORY_API`) — quando desligado, os três endpoints de analytics abaixo respondem `404`. **Requer `X-Session-Id`** (mesma regra do histórico). Ver [Decisões técnicas](#decisões-técnicas) e [PRIVACY.md](PRIVACY.md).

Métricas agregadas da sessão informada.

```json
{
  "total_analyses": 12,
  "average_score": 68.5,
  "best_score": 95,
  "worst_score": 20,
  "total_matched_skills": 34,
  "total_missing_skills": 19,
  "most_common_missing_skills": [
    { "skill_name": "docker", "count": 5 },
    { "skill_name": "aws", "count": 4 }
  ]
}
```

### `GET /api/v1/analytics/skills`

Ranking de skills por contagem de status. Query param opcional `status` (`matched`, `partial`, `missing` ou `extra`) — valor fora desse conjunto retorna `422`.

```json
{
  "items": [
    { "skill_name": "python", "matched_count": 10, "partial_count": 0, "missing_count": 1, "extra_count": 0, "total_count": 11 }
  ]
}
```

### `GET /api/v1/analytics/timeline`

Análises agrupadas por dia. Query param opcional `days` (padrão 30, entre 1 e 365).

```json
{
  "items": [
    { "date": "2026-07-03", "analyses_count": 4, "average_score": 71.25 }
  ],
  "days": 30
}
```

Nenhum dos três endpoints de analytics retorna PDF, texto bruto, hash, ou qualquer registro individual (id/created_at de uma análise específica) — apenas agregações.

---

## Decisões técnicas

- **Motor determinístico em vez de LLM na v1**: prioriza explicabilidade, testabilidade e independência de APIs pagas. Ver [Motor determinístico e explicável](#motor-determinístico-e-explicável).
- **Score ponderado (1.0 / 0.5 / 0)** em vez de correspondência binária ("tem ou não tem"): reflete melhor situações como nível de idioma parcialmente atendido.
- **Aliases e normalização de skills**: currículos e vagas usam termos diferentes para a mesma tecnologia; sem essa camada, o matching geraria falsos negativos.
- **Backend e frontend desacoplados**, comunicando via API REST: permite evoluir cada camada (ex.: adicionar dashboard no frontend, banco no backend) de forma independente.
- **Persistência via SQLAlchemy síncrono, não assíncrono** (SPEC 0004): o volume de tráfego esperado não justifica a complexidade de `AsyncSession`/`asyncpg`; a rota `POST /analyze` (assíncrona) usa uma sessão síncrona internamente, um trade-off aceitável nesta fase.
- **Falha de banco nunca quebra `/analyze`**: se o PostgreSQL estiver indisponível, a persistência é tentada, falha de forma controlada (log apenas do tipo da exceção, nunca de dados do usuário) e a análise já computada é retornada normalmente — a funcionalidade central do produto não pode depender da disponibilidade do banco nesta fase.
- **Nunca persistir PDF ou texto bruto**: apenas hashes (SHA-256), comprimentos, skills extraídas e o resultado estruturado da análise são armazenados — ver [PRIVACY.md](PRIVACY.md).
- **API de histórico desligada por padrão** (`ENABLE_HISTORY_API=false`, SPEC 0005): mesmo isolado por sessão anônima desde a SPEC 0009, não há autenticação real. Por isso fica atrás de uma feature flag, ligada apenas em testes/CI, e permanece desligada em produção até existir autenticação. Quando desligada, os endpoints respondem `404`.
- **API de analytics com flag própria** (`ENABLE_ANALYTICS_API=false`, SPEC 0006), separada de `ENABLE_HISTORY_API`: analytics expõe apenas números agregados (médias, contagens, rankings), nunca um registro individual — um perfil de risco diferente do histórico granular, por isso cada capacidade pode ser ligada de forma independente. Mesma postura de segurança: `404` quando desligada, ligada só em testes/CI.
- **Isolamento por sessão anônima via `X-Session-Id`, não cookies** (SPEC 0009): um UUID gerado no frontend (`localStorage`), enviado como header em toda chamada de histórico/analytics. Evita lidar com `SameSite`/`Secure`/CORS de cookies entre domínios diferentes (frontend na Vercel, backend no Render) e mantém o mecanismo simples e visível. `POST /analyze` aceita o header ausente/inválido (gera um UUID automaticamente); as rotas de leitura o exigem (`422` se ausente/inválido). Uma análise de outra sessão retorna `404`, nunca `403` — para não revelar sua existência. Não é um mecanismo de autenticação real — ver [PRIVACY.md](PRIVACY.md).
- **CI cobre lint, formatação, testes com cobertura (com um Postgres de teste, `ENABLE_HISTORY_API=true`, `ENABLE_ANALYTICS_API=true`) e build do frontend** (SPECs 2002, 0004, 0005, 0006 e 0009).
- **Ordenação de `list_analyses` por `created_at DESC, id DESC`, não só `created_at DESC`** (SPEC 0010): análises criadas em sucessão rápida podem receber o mesmo `created_at` até o microssegundo (observado na verificação da SPEC 0009 contra PostgreSQL real), tornando a ordenação por data isolada não-determinística em empates; `id` (chave primária, já indexada) desempata sem introduzir nova coluna.
- **CORS revisado e mantido como estava na SPEC 0010**: `get_cors_allowed_origins()` já restringia a origem a `FRONTEND_ORIGIN` fora de `ENVIRONMENT=development` desde antes desta Spec; a revisão confirmou que nenhuma mudança de código era necessária, apenas documentar a decisão de manter as flags de histórico/analytics desligadas em produção (ver checklist acima e [PRIVACY.md](PRIVACY.md)).
- **Matching semântico atrás de feature flag e dependência isolada** (`ENABLE_SEMANTIC_MATCHING=false`, SPEC 0011): `sentence-transformers` fica só em `requirements-dev.txt` — nunca na imagem de produção — porque traz `torch` como dependência transitiva (centenas de MB), peso incompatível com o plano gratuito do Render atual. Import sempre lazy/protegido por `try/except`, então ligar a flag sem a dependência instalada não quebra nada (fallback).
- **Score híbrido fixo em 70% determinístico + 30% semântico** (SPEC 0011): valores fixos no código, não configuráveis por variável de ambiente — evita mais uma variável para documentar/testar sem um pedido concreto de configurabilidade. `semantic_matches` limitado a 10 itens exibidos (o cálculo de `semantic_score` considera todas as aproximações encontradas, não só as 10 exibidas).
- **Threshold de similaridade semântica calibrado empiricamente em `0.50`** (era `0.70` na SPEC 0011, sem evidência; recalibrado na SPEC 0013 com 27 pares positivos + 17 negativos — zero falsos positivos em todos os thresholds testados, com o maior falso positivo candidato em `0.40`, e melhor F1 em `0.50`). Ver seção "Calibração do matching semântico (SPEC 0013)" acima.
- **Contrato de `POST /analyze` estendido de forma aditiva, nunca quebrado** (SPEC 0011): `semantic_score`/`hybrid_score`/`semantic_matches` são opcionais; `response_model_exclude_none=True` garante que ficam ausentes do JSON (não `null`) quando a flag está desligada ou o serviço de embeddings falha — resposta idêntica à anterior a esta Spec nesses casos.
- **Feedback via LLM local (Ollama), não API paga** (`ENABLE_LLM_FEEDBACK=false`, SPEC 0014): diferente da SPEC 0011, o problema não é peso de dependência Python (`httpx`, usado para chamar o Ollama, já está em `requirements.txt`) — é que o processo Ollama simplesmente não existe no ambiente de deploy atual. O LLM só lê o resultado já calculado (score, skills, insights) para gerar texto explicativo — nunca decide score ou matching. Fallback em 5 camadas (flag desligada, provider não suportado, Ollama inacessível, timeout de 20s, resposta fora do schema esperado) garante que `/analyze` nunca quebra por causa desta camada.
- **Validação estrita da resposta do LLM, com tolerância a campos extras** (SPEC 0014): os 4 campos (`llm_summary`, `llm_improvement_plan`, `llm_study_suggestions`, `llm_resume_tips`) são obrigatórios com o tipo correto para a resposta ser aceita; campos além desses são ignorados, não invalidam a resposta. Listas limitadas a 5 itens cada, mesmo padrão de `semantic_matches`/`insights`.

---

## Limitações atuais

Mesmo com matching avançado, o projeto ainda possui limitações conhecidas e intencionais nesta versão:

- não mede profundidade real de experiência;
- não identifica senioridade automaticamente;
- não sabe se a skill foi usada profissionalmente ou apenas citada;
- não entende contexto semântico complexo (ex.: sinônimos não cadastrados, currículos em formatos não convencionais);
- não faz OCR em PDFs baseados em imagem;
- não reescreve o currículo automaticamente;
- não substitui avaliação humana de recrutadores;
- não possui autenticação real; desde a SPEC 0009, o histórico/analytics são isolados por sessão anônima (`X-Session-Id`, gerado no navegador), mas isso não substitui login — a UI de Histórico e Dashboard (SPEC 0007) já existe e funciona **localmente**, mas os dados só carregam se as feature flags do backend estiverem ligadas (`ENABLE_HISTORY_API=false`, `ENABLE_ANALYTICS_API=false` por padrão) — no deploy público, ficam desligadas até existir autenticação real;
- desde a SPEC 0011, existe matching semântico via embeddings, mas **desligado por padrão em produção** (`ENABLE_SEMANTIC_MATCHING=false`) — ver seção "Matching semântico com embeddings" acima.
- desde a SPEC 0014, existe feedback textual assistido por LLM (Ollama local), mas **desligado por padrão em produção** (`ENABLE_LLM_FEEDBACK=false`) — o LLM só explica o resultado já calculado, nunca decide score ou matching; ver seção "Feedback textual via LLM local" acima.

Essas limitações são intencionais na v1, para manter o projeto explicável, simples de testar e evolutivo.

---

## Roadmap

O que está planejado, mas **ainda não implementado**:

- **Histórico e Dashboard em produção** — a API (SPECs 0005/0006), o isolamento por sessão anônima (SPEC 0009) e a UI de frontend (SPEC 0007) já existem e funcionam localmente; falta autenticação real para ligar as feature flags no deploy público com segurança de verdade (a sessão anônima isola por navegador, mas não autentica ninguém).
- **Matching semântico em produção** — a camada de embeddings (SPEC 0011) já existe e funciona localmente/CI; falta reavaliar o plano de hospedagem (a dependência é pesada demais para o plano gratuito do Render atual) antes de ligar `ENABLE_SEMANTIC_MATCHING` em produção.
- **LLM em produção** — o feedback textual via Ollama local (SPEC 0014) já existe e funciona localmente; não é promovido a produção porque Ollama é um processo externo que não existe no ambiente de deploy atual (Render). Reescrita de trechos do currículo, carta de apresentação e plano de estudos narrativo continuam fora do escopo desta camada (ver "Fora do escopo" da SPEC 0014).
- Suporte a DOCX e OCR para PDFs escaneados;
- Comparação com múltiplas vagas;
- Exportação de resultado em PDF;
- Autenticação de usuários.

> Embeddings (matching semântico, SPEC 0011) e LLM (feedback local via Ollama, SPEC 0014) **já existem, estão implementados e testados** — o que falta é levá-los a produção (ver os itens acima e [Local-only features](#local-only-features)), não implementá-los.

---

## Relevância para portfólio

Este projeto foi construído para demonstrar, de ponta a ponta, práticas de engenharia de software e de IA aplicada a um problema real — API REST documentada, persistência real, testes contra banco de verdade, feature flags com fallback testado, e duas camadas de IA (embeddings calibrados empiricamente e LLM local) implementadas com o mesmo rigor do resto do sistema, ainda que deliberadamente desligadas em produção. Ver [Architecture highlights](#architecture-highlights), [AI Engineering highlights](#ai-engineering-highlights) e [Software Engineering highlights](#software-engineering-highlights) acima para o detalhamento — esta seção não repete o conteúdo delas.

---

## O que aprendi

Construir este projeto envolveu decisões de trade-off recorrentes em produtos reais: priorizar explicabilidade em vez de sofisticação (motor determinístico antes de LLM), desenhar uma API que sobrevive à evolução do produto (aliases e schemas pensados para crescer), e tratar infraestrutura como parte do produto desde cedo (Docker e CI antes de novas features, não depois). Também reforçou a importância de documentar honestamente o que existe versus o que é roadmap — tentação recorrente em projetos de portfólio é superestimar capacidades de IA antes delas existirem de fato.

---

## English Summary

**AI Career Intelligence Platform** (evolved from **AI Resume Analyzer**) is a full-stack application that compares a PDF résumé against a job description and returns an explainable compatibility score, matched/missing/partial/extra skills, and actionable recommendations. The core engine is **deterministic, explainable and fully tested** (regex-based skill extraction, aliases, weighted matching) — the score itself never depends on any ML model. The project also includes two optional, additive AI layers, both implemented, tested and empirically evaluated: a **semantic matching layer** using local embeddings (`sentence-transformers`/`all-MiniLM-L6-v2`, threshold calibrated on 44 labeled pairs) and a **local LLM feedback layer** via Ollama for natural-language explanations. Both are **disabled by default in production** — not because they don't work, but because of documented, deliberate constraints (deploy weight for embeddings, no external LLM process available in the current hosting plan for Ollama) — see [Local-only features](#local-only-features). Stack: FastAPI + PyMuPDF + Pydantic + SQLAlchemy/PostgreSQL on the backend, React + Vite on the frontend, 243 automated tests (pytest, including integration tests against a real PostgreSQL instance), Docker/Docker Compose for local development, and GitHub Actions CI validating tests and build on every push/PR. Live demo links are in the [Demo](#demo) section above.

---

## Contribuição

Contribuições são bem-vindas. Antes de abrir um Pull Request, veja [CONTRIBUTING.md](CONTRIBUTING.md) para os comandos de lint, formatação e testes que o CI executa.

```bash
git checkout -b feature/minha-feature
git commit -m "feat: adiciona minha feature"
git push origin feature/minha-feature
```

Depois, abra um Pull Request.

---

## Licença

Este projeto está sob a licença MIT.

Para detalhes sobre como os dados enviados (currículo e descrição da vaga) são tratados, ver [PRIVACY.md](PRIVACY.md).

---

## Autoria

Desenvolvido como projeto de portfólio com foco em Python, FastAPI, React, APIs modernas, frontend responsivo, testes automatizados, containerização, CI e análise determinística de currículos e vagas — evoluindo para uma plataforma mais completa de inteligência de carreira.
