# Roadmap — AI Career Intelligence Platform

O que está planejado, mas ainda não implementado (ou implementado apenas localmente, não em produção). O README principal traz a versão resumida — este documento detalha o motivo e o contexto de cada item.

## Levar capacidades já implementadas para produção

- **Histórico e Dashboard em produção** — a API, o isolamento por sessão anônima e a UI de frontend já existem e funcionam localmente; falta autenticação real para ligar as feature flags no deploy público com segurança de verdade (a sessão anônima isola por navegador, mas não autentica ninguém).
- **Matching semântico em produção** — a camada de embeddings já existe e funciona localmente/CI; falta reavaliar o plano de hospedagem (a dependência é pesada demais para o plano gratuito atual) antes de ligar a flag em produção.
- **Feedback via LLM em produção** — já existe e funciona localmente; não é promovido a produção porque depende de um processo Ollama que não existe no ambiente de deploy atual.
- **Dashboard "production-safe"** — uma versão do histórico/analytics que possa ser exposta publicamente sem depender de autenticação forte (ex.: retenção curta, agregação sem detalhe individual).

## Frontend e visualização

- **Gráficos profissionais no frontend** — visualizações mais ricas para o dashboard (hoje usa componentes simples, sem biblioteca de gráficos).
- **Radar de skills** — visualização comparando o perfil do candidato com o perfil ideal da vaga.
- **Evolução longitudinal do Career Improvement Plan** — hoje o plano é gerado por análise individual; uma versão futura pode comparar gaps recorrentes entre várias análises.

## Motor de análise

- **Comparação com múltiplas vagas simultaneamente** — hoje a análise é sempre 1 currículo × 1 vaga.
- Suporte a DOCX e OCR para PDFs baseados em imagem.

## Já implementado recentemente

- **Distinção entre requisitos obrigatórios, desejáveis e menções negadas** — o motor contextual já diferencia `required`, `optional` e `ignored` na descrição da vaga, com score explicável.
- **Detecção de senioridade explícita da vaga** — o parser contextual já identifica termos como `junior`, `pleno/mid-level`, `senior`, `lead`, `staff` e `principal` na descrição da vaga.
- **Career Improvement Plan por análise** — o backend já gera um plano determinístico a partir de `missing_skills` e `partial_skills`, e o frontend renderiza o campo quando ele existe.

## Produto

- Exportação do resultado da análise em PDF.
- Autenticação de usuários (pré-requisito para levar histórico/analytics/dashboard a produção com segurança real).

## Como este roadmap se relaciona com o que já existe

Nenhum item acima é uma limitação de arquitetura — o padrão de feature flag + fallback testado já é usado em 4 capacidades opcionais (histórico, analytics, matching semântico, LLM), então adicionar a próxima capacidade segue o mesmo caminho já validado. O que falta em cada item é, na maioria dos casos, uma decisão de produto (vale o custo de infraestrutura ou de complexidade?) mais do que uma limitação técnica.
