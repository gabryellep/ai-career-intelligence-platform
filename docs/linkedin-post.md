# Texto para LinkedIn — AI Career Intelligence Platform

Dois textos prontos para postagem, com o mesmo compromisso de honestidade do resto do repositório: nenhuma promessa de contratação, nenhuma afirmação de que embeddings/LLM rodam em produção, nenhuma menção a autenticação real (não existe). Ajuste links e detalhes antes de publicar, se necessário.

---

## Versão curta

Nos últimos meses construí o **AI Career Intelligence Platform**: uma plataforma que compara um currículo em PDF com uma descrição de vaga e devolve um score de compatibilidade explicável — skills atendidas, faltantes e parciais, além de recomendações práticas.

A decisão técnica mais importante do projeto: comecei com um motor 100% determinístico e explicável (regras, aliases, matching ponderado) — sem IA generativa, sem "caixa preta" — porque queria um resultado auditável antes de qualquer coisa. Só depois adicionei, como camadas **opcionais** e aditivas: matching semântico via embeddings (calibrado empiricamente, com métricas reais de precision/recall) e feedback textual via LLM rodando localmente (Ollama) — nenhum dos dois altera o score determinístico, e ambos ficam desligados por padrão em produção por razões documentadas (peso de deploy e ausência de infraestrutura para um LLM local, respectivamente).

Stack: FastAPI + PostgreSQL no backend, React no frontend, 277 testes automatizados, CI com GitHub Actions, deploy real (Render + Vercel).

Repositório: https://github.com/gabryellep/ai-resume-analyzer
Demo: https://ai-career-intelligence-platform-beta.vercel.app/

#Python #FastAPI #React #IA #SoftwareEngineering #Portfolio

---

## Versão técnica/detalhada

Passei os últimos meses evoluindo um projeto de portfólio — **AI Career Intelligence Platform** — e quero compartilhar algumas decisões de engenharia que considero relevantes para quem trabalha com IA aplicada.

**O problema**: candidatos raramente sabem, de forma objetiva, o quanto seu currículo atende a uma vaga específica, nem quais gaps priorizar antes de se candidatar.

**A decisão de base**: em vez de partir direto para um LLM, construí primeiro um motor determinístico — extração de skills por regex/dicionário, aliases (ex.: "K8s" → "Kubernetes"), matching ponderado, score explicável passo a passo. Essa decisão foi deliberada: eu queria um baseline auditável e testável antes de adicionar qualquer camada de IA — e documentei o porquê no próprio README do projeto.

**Depois, duas camadas de IA, como capacidades opcionais e aditivas** — nunca como substituto do motor determinístico:

1. **Matching semântico via embeddings** (`sentence-transformers`/`all-MiniLM-L6-v2`, rodando localmente): para capturar sinônimos que o dicionário de aliases não cobre (ex.: "containers" ≈ "Docker"). Em vez de escolher um threshold de similaridade por intuição, criei um script de calibração que testa 5 thresholds candidatos contra 44 pares de skills rotulados (positivos e negativos, incluindo "armadilhas" como `java` vs. `javascript`), medindo precision, recall e F1 de verdade. O resultado real: o threshold inicial (0.70) tinha recall baixíssimo; reduzi para 0.50 com base nos números, sem introduzir nenhum falso positivo na amostra testada.

2. **Feedback textual via LLM local (Ollama)**: para reescrever o resultado estruturado em linguagem mais natural. O LLM só lê o resultado já calculado — nunca decide score ou matching — e a resposta passa por validação estrita de schema antes de ser aceita; qualquer coisa fora do formato esperado (ou qualquer falha de conexão/timeout) faz o sistema simplesmente ignorar o feedback e responder normalmente, sem quebrar.

**Por que nenhuma das duas camadas de IA está ligada na demo pública**: não é por estarem incompletas — ambas têm testes automatizados e documentação de privacidade. É uma decisão de infraestrutura documentada: os embeddings dependem de uma biblioteca pesada (torch) incompatível com o plano gratuito de hospedagem atual; o LLM depende de um processo Ollama que simplesmente não existe no ambiente de deploy. Achei mais honesto documentar isso claramente do que fingir que está tudo ativo.

**O resto da engenharia**: API REST versionada, persistência em PostgreSQL (nunca o PDF ou o texto bruto — só hashes e metadados), isolamento por sessão anônima (não é autenticação real, e digo isso explicitamente na documentação), 277 testes automatizados (incluindo testes de integração contra um Postgres real, não só mocks), CI no GitHub Actions, deploy real no Render + Vercel.

Não é um projeto que promete "revolucionar recrutamento" — é um exercício de engenharia honesta: motor explicável primeiro, IA depois, com evidência antes de cada decisão que impacta o usuário.

Repositório: https://github.com/gabryellep/ai-resume-analyzer
Demo: https://ai-career-intelligence-platform-beta.vercel.app/

#Python #FastAPI #React #MachineLearning #Embeddings #LLM #Ollama #SoftwareEngineering #AIEngineering #Portfolio
