# Privacidade e tratamento de dados

Este documento descreve, de forma honesta e objetiva, como o **AI Career Intelligence Platform** (repositório `ai-resume-analyzer`) trata os dados enviados pelo usuário na versão atual. Ele foi atualizado na SPEC 0004, quando a aplicação passou a persistir metadados de cada análise — antes disso, nada era armazenado. Este documento será atualizado novamente sempre que o tratamento de dados mudar.

## O que é enviado

Ao usar a aplicação, o usuário envia:

- um arquivo PDF de currículo, que pode conter dados pessoais como nome, e-mail, telefone, endereço, formação, experiências profissionais e links (LinkedIn, GitHub etc.);
- o texto de uma descrição de vaga.

## Como esses dados são processados

1. O PDF é recebido pela API (`POST /analyze`) e mantido **apenas em memória**, durante a própria requisição — nunca salvo em disco.
2. O texto é extraído do PDF (via PyMuPDF) para identificar skills, idiomas e outras informações relevantes à comparação com a vaga.
3. A resposta (score, skills, insights, recomendações) é devolvida ao usuário na mesma requisição.
4. **A partir da SPEC 0004**, um registro estruturado dessa análise é salvo em um banco de dados PostgreSQL — ver seção abaixo para o que exatamente é armazenado.

## O que passa a ser armazenado (desde a SPEC 0004)

Para cada análise bem-sucedida, o sistema grava:

- um **hash SHA-256** do arquivo PDF enviado (não o arquivo em si);
- um **hash SHA-256** e o **comprimento** do texto extraído do currículo (não o texto em si);
- um **hash SHA-256** e o **comprimento** da descrição da vaga (não o texto em si);
- as **skills técnicas identificadas na vaga** (ex.: "python", "docker") — nomes de tecnologias, não dado pessoal;
- o **score de compatibilidade**, as **skills classificadas** (matched/partial/missing/extra), os **insights** e as **recomendações** gerados pelo motor determinístico — ou seja, o mesmo resultado estruturado que já é devolvido na resposta da API.

Hashes servem apenas para rastreabilidade técnica (ex.: identificar se duas análises usaram o mesmo arquivo) — não é possível reconstituir o conteúdo original do currículo ou da vaga a partir de um hash SHA-256.

## O que **continua não acontecendo** nesta versão

- O arquivo PDF **nunca é salvo**, nem em disco, nem no banco de dados, em nenhum formato.
- O texto completo extraído do currículo **nunca é armazenado** — apenas seu hash e comprimento.
- O texto completo da descrição da vaga **nunca é armazenado** — apenas seu hash, comprimento e as skills identificadas nele.
- Nenhum dado do currículo ou da vaga é registrado em logs do servidor — inclusive falhas de conexão com o banco são logadas apenas pelo tipo do erro, nunca com conteúdo do usuário.
- Nenhum dado é compartilhado com terceiros, serviços de IA externos ou APIs de terceiros — toda a análise é feita localmente pelo próprio backend, com um motor determinístico. Desde a SPEC 0014, existe uma camada **opcional** de feedback textual via LLM, mas ela roda **localmente** via Ollama (nunca uma API paga de terceiros) e fica desligada por padrão — ver seção própria abaixo.
- Não há criação de conta, login ou qualquer identificação do usuário — as análises armazenadas não são vinculadas a nenhuma pessoa.
- **Ainda não existe** nenhuma forma de o usuário solicitar exclusão dos dados armazenados, nem retenção com prazo definido — isso é planejado para uma fase futura, quando este documento será atualizado novamente com uma política de retenção e exclusão.
- Se o banco de dados estiver indisponível no momento de uma análise, a aplicação **continua respondendo normalmente ao usuário** — a persistência falha silenciosamente (registrada apenas em log técnico), sem impedir o uso do produto.

## Isolamento por sessão anônima (desde a SPEC 0009)

Antes da SPEC 0009, o histórico e os analytics eram **globais**: qualquer cliente da API veria dados de qualquer pessoa. A partir desta Spec, cada análise passa a ser marcada com um `session_id` — um UUID gerado automaticamente pelo navegador na primeira vez que a aplicação é usada, salvo em `localStorage`, e enviado em todas as chamadas relevantes através do header `X-Session-Id`.

**O que o `session_id` é e não é**:
- É um identificador anônimo de **navegador/origem**, não de uma pessoa — não há nome, e-mail ou qualquer dado de identificação associado a ele.
- Fica salvo em `localStorage` do navegador. **Limitações**: se você limpar os dados do site, usar outro navegador, uma aba anônima, ou outro dispositivo, um novo `session_id` é gerado e o histórico anterior deixa de ser acessível através da interface (embora continue existindo no banco, sem forma de recuperação sem o UUID original).
- **Não é um mecanismo de segurança forte.** Não há senha, assinatura ou verificação de posse — quem souber (ou conseguir de alguma forma) o UUID de outra sessão consegue ler os dados daquela sessão através da API. Trate-o como um identificador de conveniência para separar históricos em um cenário de uso casual/portfólio, não como proteção contra um atacante determinado.

## Consulta ao histórico de análises (desde a SPEC 0005)

Existem dois endpoints de leitura: `GET /api/v1/analyses` (lista paginada, com filtros por score mínimo e por skill) e `GET /api/v1/analyses/{id}` (detalhe de uma análise). Ambos retornam exatamente os mesmos dados descritos na seção "O que passa a ser armazenado" acima (score, skills, insights, recomendações, data) — **nunca** PDF, texto bruto ou hashes. Desde a SPEC 0009, ambos exigem o header `X-Session-Id` e retornam apenas análises daquela sessão — `422` se o header estiver ausente ou for inválido; `404` (nunca `403`) para uma análise que existe mas pertence a outra sessão.

**Mitigação em camadas**: os endpoints de histórico ficam **desligados por padrão**, controlados pela variável de ambiente `ENABLE_HISTORY_API` (`false` por padrão). Quando desligados, respondem `404`, como se não existissem. Eles só são ligados (`ENABLE_HISTORY_API=true`) em ambiente de testes/CI — **no deploy público, permanecem desligados até que autenticação real seja implementada**, já que o isolamento por sessão anônima (acima) não substitui autenticação de verdade.

## Analytics agregada (desde a SPEC 0006)

Existem três endpoints de agregação: `GET /api/v1/analytics/summary` (total de análises, score médio/melhor/pior, skills mais faltantes), `GET /api/v1/analytics/skills` (ranking de skills por status matched/partial/missing/extra) e `GET /api/v1/analytics/timeline` (análises agrupadas por dia). Todos retornam apenas números agregados e nomes de skills — **nunca** um registro individual, PDF, texto bruto ou hashes. Desde a SPEC 0009, os três também exigem `X-Session-Id` e calculam as métricas apenas com as análises daquela sessão.

**Mitigação em camadas**: os endpoints de analytics ficam **desligados por padrão**, controlados por uma variável de ambiente **própria e separada** da do histórico: `ENABLE_ANALYTICS_API` (`false` por padrão). Essa separação existe porque analytics agregada tem um perfil de risco diferente do histórico granular — um operador pode querer ligar uma capacidade sem a outra. Quando desligados, os endpoints respondem `404`. Só são ligados (`ENABLE_ANALYTICS_API=true`) em testes/CI — **no deploy público, permanecem desligados até que autenticação real seja implementada**.

## Consentimento

O frontend exige que o usuário marque uma caixa de consentimento antes de enviar o currículo. A partir da SPEC 0004, esse consentimento cobre também o armazenamento dos metadados descritos acima (hashes, score, skills, insights e recomendações) — nunca o PDF ou o texto bruto.

## Validações de segurança aplicadas ao upload

Para reduzir o risco de upload de arquivos maliciosos ou disfarçados, o backend valida, antes de processar qualquer arquivo:

- extensão do nome do arquivo (quando informado pelo cliente);
- tipo MIME declarado;
- assinatura binária do arquivo (magic bytes `%PDF-`), confirmando que o conteúdo é de fato um PDF;
- tamanho máximo de 5 MB;
- rejeição de arquivos vazios.

Essas validações reduzem riscos comuns, mas não eliminam todos os riscos possíveis de upload de arquivos — ver limitações abaixo.

## Limitações conhecidas desta versão

- Não há rate limiting (proteção contra volume excessivo de requisições).
- Não há verificação de antivírus/malware no conteúdo do PDF.
- A validação de magic bytes confirma a assinatura do arquivo, mas não garante que o PDF esteja livre de conteúdo malicioso embutido.
- Não há criptografia em trânsito própria da aplicação (depende do HTTPS fornecido pela infraestrutura de deploy).

## Matching semântico via embeddings (desde a SPEC 0011)

Desde a SPEC 0011, existe uma camada opcional de matching semântico, desligada por padrão (`ENABLE_SEMANTIC_MATCHING=false`, inclusive em produção), que usa o modelo `sentence-transformers`/`all-MiniLM-L6-v2` para aproximar skills que o dicionário de aliases do motor determinístico não cobre.

**O que é calculado (apenas em memória, por requisição, quando a flag está ligada)**:
- Embeddings são calculados **somente sobre nomes de skills** (ex.: `"docker"`, `"machine learning"`) — nunca sobre o texto do currículo ou da vaga.
- Os vetores de embedding em si **nunca são persistidos** — servem apenas para calcular uma similaridade de cosseno (um float), descartada da memória ao final da requisição.

**O que passa a ser armazenado (apenas quando a flag está ligada e o cálculo é bem-sucedido)**:
- `semantic_score` e `hybrid_score` (inteiros, 0–100);
- `semantic_matches`: uma lista de até 10 itens, cada um com apenas `job_skill` (nome de skill), `matched_resume_skill` (nome de skill) e `similarity` (float) — nunca texto bruto, nunca um vetor de embedding.

Com a flag desligada (padrão em produção) ou em caso de falha do serviço de embeddings, essas três colunas ficam `NULL` — mesmo padrão de privacidade e de resiliência já aplicado a `match_details` e à persistência em geral (ver seções acima).

## Feedback textual via LLM local (desde a SPEC 0014)

Desde a SPEC 0014, existe uma camada opcional de feedback textual, desligada por padrão (`ENABLE_LLM_FEEDBACK=false`, inclusive em produção), que usa um LLM open-source rodando **localmente** via [Ollama](https://ollama.com/) (modelo padrão: `llama3.1`) para reescrever o resultado da análise em linguagem mais natural.

**O que é enviado ao modelo local (apenas quando a flag está ligada)**: exclusivamente dados já estruturados e já calculados pelo motor determinístico/semântico — `score`, `matched_skills`, `missing_skills`, `partial_skills`, `extra_skills`, `insights` (pontos fortes/fracos) e, se existirem, `semantic_score`/`hybrid_score`. **Nunca** é enviado: o PDF, o texto extraído do currículo, o texto da descrição da vaga, qualquer hash (`pdf_sha256`, `resume_text_sha256`, `description_sha256`) ou o `session_id`.

**O que passa a ser armazenado (apenas quando a flag está ligada e a resposta do modelo é válida)**:
- `llm_summary`: um parágrafo curto gerado pelo modelo;
- `llm_improvement_plan`, `llm_study_suggestions`, `llm_resume_tips`: listas de até 5 itens cada.

**O que nunca é armazenado**: o prompt completo enviado ao modelo, nem a resposta bruta antes da validação — apenas os 4 campos já validados acima (mesma política de minimização de dados aplicada a `match_details`/`semantic_matches`).

**Importante — o LLM é local, não um serviço de terceiros**: quando a flag está ligada, os dados acima são enviados para um processo Ollama rodando na própria máquina de quem ligou a flag (`http://localhost:11434` por padrão) — nunca para uma API externa como OpenAI ou Anthropic. Isso significa que, mesmo com a flag ligada, nenhum dado sai da máquina onde o backend e o Ollama estão rodando.

Com a flag desligada (padrão em produção) ou em caso de falha do serviço (Ollama indisponível, timeout, resposta inválida), essas quatro colunas ficam `NULL` — mesmo padrão de resiliência já aplicado ao matching semântico (SPEC 0011).

## Decisão de deploy registrada (SPEC 0010, 2026-07-03)

Ao preparar o deploy público, foi avaliado — e recusado, por ora — habilitar `ENABLE_HISTORY_API` e `ENABLE_ANALYTICS_API` em produção. A decisão registrada é:

- `ENABLE_HISTORY_API=false` e `ENABLE_ANALYTICS_API=false` em produção, mantendo o padrão já existente desde as SPECs 0005/0006.
- O Histórico e o Dashboard (SPEC 0007) continuam disponíveis **apenas em ambiente local/dev**, com as flags ligadas manualmente (ver README, seção "Histórico e Dashboard").
- **Justificativa**: o isolamento por `X-Session-Id` (SPEC 0009) melhora a separação entre sessões de navegador, mas **não é autenticação forte** — ainda faltam expiração de sessão, revogação, rate limiting e autenticação real de usuário. Habilitar os endpoints em produção antes disso exporia histórico/analytics a qualquer pessoa que descobrisse ou reutilizasse um `X-Session-Id` alheio.
- Esta Spec também corrigiu uma falha de ordenação determinística em `list_analyses` (`created_at DESC, id DESC`, antes só `created_at DESC`) e revisou o CORS de produção, confirmando que já estava corretamente restrito a `FRONTEND_ORIGIN` — nenhuma mudança de política de acesso foi necessária.
- Esta decisão será revisitada quando autenticação real (login, JWT ou equivalente) existir — só então o histórico e os analytics serão considerados para produção.

## Mudanças futuras

Quando autenticação real for implementada, este documento será atualizado para descrever: por quanto tempo os dados ficam armazenados, como o usuário pode solicitar exclusão, e como as sessões anônimas existentes (ver "Isolamento por sessão anônima" acima) passam a se relacionar com contas reais. Até lá, os endpoints de histórico e de analytics permanecem desligados em produção (`ENABLE_HISTORY_API=false`, `ENABLE_ANALYTICS_API=false`), mesmo já sendo isolados por sessão de navegador. O matching semântico (`ENABLE_SEMANTIC_MATCHING=false`, SPEC 0011) permanece desligado em produção por um motivo diferente — peso da dependência para o plano de hospedagem atual, não uma questão de autenticação — mas será reavaliado junto das demais flags quando a infraestrutura de deploy mudar. O feedback via LLM (`ENABLE_LLM_FEEDBACK=false`, SPEC 0014) também permanece desligado em produção por um motivo próprio — o processo Ollama não existe no ambiente de deploy atual — independente de autenticação ou peso de dependência Python.

## Contato

Em caso de dúvidas sobre este documento ou sobre o tratamento de dados desta aplicação, entre em contato através do repositório no GitHub: https://github.com/gabryellep/ai-resume-analyzer
