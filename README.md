# AI Resume Analyzer

> Analise a compatibilidade entre um currículo em PDF e uma descrição de vaga com um score explicável, identificação de skills, análise de pontos fortes e recomendações práticas de melhoria.

---

## Demo

- **Frontend:** https://ai-resume-analyzer-app-pi.vercel.app  
- **Backend/API:** https://ai-resume-analyzer-wh05.onrender.com  
- **Documentação da API:** https://ai-resume-analyzer-wh05.onrender.com/docs  

> Observação: o backend está hospedado em plano gratuito no Render. Em alguns acessos, a primeira requisição pode demorar alguns segundos porque o serviço pode “acordar” após um período de inatividade.

---

## Badges

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)
![Pytest](https://img.shields.io/badge/Tests-pytest-0A9EDC?style=flat)
![Deploy](https://img.shields.io/badge/Deploy-Render%20%2B%20Vercel-purple?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Sobre o Projeto

O **AI Resume Analyzer** é uma aplicação web full-stack que compara um currículo em PDF com a descrição de uma vaga de emprego.

O sistema extrai o texto do currículo, identifica skills técnicas, idiomas e aliases, compara essas informações com os requisitos da vaga e gera uma análise de compatibilidade com:

- score de compatibilidade;
- skills encontradas;
- skills faltantes;
- skills parcialmente atendidas;
- skills extras presentes no currículo;
- pontos fortes;
- pontos de atenção;
- próximos passos recomendados;
- recomendações práticas para melhorar o currículo.

A proposta do projeto é criar uma análise simples de usar, visualmente clara e tecnicamente explicável, sem depender de uma IA generativa na versão atual.

---

## Objetivo

O objetivo do projeto é ajudar candidatos a entenderem o quanto seu currículo está alinhado com uma vaga específica.

Em vez de retornar apenas uma pontuação genérica, o sistema tenta responder perguntas como:

- Quais requisitos da vaga meu currículo já atende?
- Quais skills estão faltando?
- Existe alguma skill parcialmente atendida?
- Quais pontos do currículo podem ser destacados?
- Quais melhorias devo priorizar antes de me candidatar?
- Meu currículo apresenta habilidades extras que podem ser diferenciais?

---

## Funcionalidades

- Upload de currículo em PDF;
- Leitura automática do conteúdo do PDF;
- Campo para colar a descrição da vaga;
- Extração de skills técnicas com regex;
- Dicionário com mais de 100 skills;
- Suporte a aliases e sinônimos;
- Detecção de idioma com níveis;
- Score de compatibilidade de 0 a 100;
- Matching avançado entre currículo e vaga;
- Identificação de:
  - skills atendidas;
  - skills faltantes;
  - skills parcialmente atendidas;
  - skills extras;
- Recomendações práticas baseadas nos gaps encontrados;
- Seção de análise do perfil com pontos fortes, pontos de atenção e próximos passos;
- Interface responsiva;
- API REST com FastAPI;
- Documentação automática via Swagger;
- Testes automatizados com pytest.

---

## Diferenciais do Projeto

Este projeto não é apenas um formulário com upload de PDF. Ele possui uma lógica de análise estruturada e explicável.

Principais diferenciais:

- análise determinística e testável;
- score ponderado;
- suporte a skills parcialmente atendidas;
- tratamento de níveis de inglês;
- aliases para reduzir falsos negativos;
- insights estruturados para o usuário;
- recomendações mais acionáveis;
- backend e frontend separados;
- código modular;
- testes automatizados;
- deploy real com frontend e backend online.

---

## Stack Utilizada

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Extração de PDF | PyMuPDF |
| Validação | Pydantic v2 |
| Frontend | React 18, Vite |
| Estilização | CSS puro |
| Testes | pytest, httpx |
| Deploy Backend | Render |
| Deploy Frontend | Vercel |

---

## Arquitetura Geral

O projeto é dividido em duas partes principais:

```text
ai-resume-analyzer/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   └── tests/
│
└── frontend/
    ├── src/
    ├── package.json
    ├── vite.config.js
    └── index.html
```

O backend é responsável por processar os dados, extrair texto, identificar skills e gerar a análise.

O frontend é responsável por receber o PDF e a descrição da vaga, enviar os dados para a API e exibir o resultado de forma visual e organizada.

---

## Como a Análise Funciona

O fluxo da análise é:

```text
Currículo em PDF + descrição da vaga
        ↓
Extração de texto do PDF
        ↓
Extração de skills do currículo e da vaga
        ↓
Normalização de skills e aliases
        ↓
Matching avançado
        ↓
Cálculo do score ponderado
        ↓
Geração de insights
        ↓
Geração de recomendações
        ↓
Exibição visual no frontend
```

---

## Extração de Skills

O sistema utiliza um dicionário de skills técnicas e padrões com regex para identificar termos relevantes no currículo e na vaga.

Exemplos de skills detectadas:

- Python;
- JavaScript;
- TypeScript;
- FastAPI;
- React;
- Docker;
- Kubernetes;
- AWS;
- PostgreSQL;
- Pandas;
- Machine Learning;
- GitHub Actions;
- CI/CD;
- inglês básico/intermediário/avançado.

---

## Aliases e Sinônimos

Para reduzir falsos negativos, o sistema trata alguns termos equivalentes como a mesma skill.

Exemplos:

| Termo encontrado | Skill canônica |
|---|---|
| Amazon Web Services | AWS |
| Postgres | PostgreSQL |
| Postgres SQL | PostgreSQL |
| NodeJS | Node.js |
| JS | JavaScript |
| TS | TypeScript |
| CI CD | CI/CD |
| Machine-learning | Machine Learning |
| K8s | Kubernetes |
| Sklearn | Scikit-learn |

Isso torna a análise mais flexível, já que currículos e vagas podem usar formas diferentes para se referir à mesma tecnologia.

---

## Detecção de Idiomas

O projeto também possui suporte básico a idiomas, especialmente inglês.

O sistema diferencia níveis de inglês:

| Texto encontrado | Interpretação |
|---|---|
| inglês / english | english_basic |
| inglês intermediário / intermediate english / B1 / B2 | english_intermediate |
| inglês avançado / advanced english / fluent english / C1 / C2 | english_advanced |

Essa lógica evita que o sistema considere automaticamente qualquer menção a “inglês” como inglês avançado.

Exemplo:

```text
Vaga:
Python, Docker e inglês avançado C1

Currículo:
Python e inglês intermediário B2
```

Resultado esperado:

```text
Python → atendido
Docker → ausente
Inglês avançado → parcialmente atendido
```

---

## Matching Avançado

O sistema classifica as skills em quatro grupos:

### Skills encontradas

Skills exigidas pela vaga e presentes no currículo.

Exemplo:

```text
Vaga pede: Python
Currículo tem: Python
Resultado: skill encontrada
```

### Skills faltantes

Skills exigidas pela vaga, mas não encontradas no currículo.

Exemplo:

```text
Vaga pede: Docker
Currículo não menciona Docker
Resultado: skill faltante
```

### Skills parcialmente atendidas

Skills que aparecem no currículo, mas não atendem completamente o nível exigido pela vaga.

Exemplo:

```text
Vaga pede: inglês avançado
Currículo tem: inglês intermediário
Resultado: skill parcialmente atendida
```

### Skills extras

Skills presentes no currículo, mas não exigidas diretamente na vaga.

Exemplo:

```text
Currículo tem: Machine Learning
Vaga não menciona Machine Learning
Resultado: skill extra
```

Essas skills extras podem ser diferenciais em outras oportunidades, mesmo que não impactem diretamente o score da vaga atual.

---

## Cálculo do Score

O score é calculado de forma ponderada e explicável.

Cada skill da vaga recebe uma pontuação:

```text
Skill atendida completamente = 1.0 ponto
Skill parcialmente atendida = 0.5 ponto
Skill ausente = 0 ponto
```

Fórmula:

```text
score = round(pontos_obtidos / total_de_skills_exigidas * 100)
```

Exemplo:

```text
Vaga:
Python, Docker, AWS, inglês avançado

Currículo:
Python, inglês intermediário

Resultado:
Python = 1.0
Inglês avançado = 0.5
Docker = 0
AWS = 0

score = round(1.5 / 4 * 100) = 38
```

Essa abordagem permite que o sistema seja mais justo do que um simples “tem ou não tem”.

---

## Recomendações

As recomendações são geradas com base nas skills faltantes, skills parcialmente atendidas e score geral.

Exemplos de recomendações:

- Criar ou destacar um projeto prático com Docker;
- Adicionar evidências de uso de AWS em projetos;
- Informar nível de inglês com padrão CEFR, como B2, C1 ou C2;
- Reposicionar experiências relevantes no início do currículo;
- Priorizar as principais skills faltantes antes de se candidatar;
- Publicar projetos no GitHub para demonstrar experiência prática.

---

## Insights do Perfil

Além das recomendações, a aplicação gera uma seção de análise do perfil com:

### Pontos fortes

Exemplos:

- boa cobertura em linguagens de programação;
- skills diretamente alinhadas com a vaga;
- presença de tecnologias relevantes no currículo.

### Pontos de atenção

Exemplos:

- gaps em cloud e DevOps;
- idioma em nível inferior ao solicitado;
- baixa compatibilidade com os requisitos da vaga.

### Próximos passos

Exemplos:

- criar projeto prático com Docker;
- informar melhor o nível de inglês;
- adicionar 2 ou 3 skills críticas ao currículo;
- destacar projetos relevantes no topo do currículo.

---

## Por que a versão atual ainda não usa IA generativa?

A versão atual do projeto não utiliza IA generativa de propósito.

A decisão técnica foi priorizar um motor de análise determinístico, explicável e testável.

Isso significa que:

- o score pode ser explicado;
- os testes automatizados conseguem validar a lógica;
- o sistema não depende de APIs pagas;
- os resultados são mais previsíveis;
- a análise pode ser auditada e melhorada com regras claras.

A IA generativa está planejada como evolução futura, mas não para substituir o score.

A ideia é usar IA como camada adicional para:

- gerar feedback mais natural;
- sugerir melhorias no texto do currículo;
- adaptar experiências para uma vaga específica;
- sugerir reescritas;
- gerar carta de apresentação;
- explicar gaps com linguagem mais humana.

Fluxo futuro planejado:

```text
Motor determinístico
        ↓
Dados estruturados
        ↓
IA gera feedback textual personalizado
```

---

## Limitações da Versão Atual

Mesmo com matching avançado, o projeto ainda possui limitações:

- não mede profundidade real de experiência;
- não identifica senioridade automaticamente;
- não sabe se a skill foi usada profissionalmente ou apenas citada;
- não entende contexto semântico complexo;
- não faz OCR em PDFs baseados em imagem;
- não reescreve o currículo automaticamente;
- não substitui avaliação humana de recrutadores.

Essas limitações são intencionais na v1 para manter o projeto explicável, simples de testar e evolutivo.

---

## Instalação Local

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- npm 9+
- Git

---

## Rodando o Backend

Entre na pasta do backend:

```bash
cd backend
```

Crie o ambiente virtual:

```bash
python -m venv venv
```

Ative o ambiente virtual no Windows:

```bash
venv\Scripts\activate
```

Ative o ambiente virtual no macOS/Linux:

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Inicie o servidor:

```bash
uvicorn main:app --reload
```

Backend local:

```text
http://127.0.0.1:8000
```

Documentação da API:

```text
http://127.0.0.1:8000/docs
```

---

## Rodando o Frontend

Entre na pasta do frontend:

```bash
cd frontend
```

Instale as dependências:

```bash
npm install
```

Inicie o servidor de desenvolvimento:

```bash
npm run dev
```

Frontend local:

```text
http://localhost:5173
```

---

## Variáveis de Ambiente

Em produção, o frontend precisa saber a URL do backend.

Na Vercel, foi configurada a variável:

```text
VITE_API_BASE_URL=https://ai-resume-analyzer-wh05.onrender.com
```

Localmente, se essa variável não existir, o frontend usa `/analyze` com o proxy do Vite.

No Render, foram configuradas as variáveis:

```text
ENVIRONMENT=production
FRONTEND_ORIGIN=https://ai-resume-analyzer-app-pi.vercel.app
```

---

## Testes

O backend possui testes automatizados com pytest.

Para rodar os testes:

```bash
cd backend
pytest tests/ -v
```

Os testes cobrem:

- extração de PDF;
- health check;
- extração de skills;
- aliases;
- níveis de inglês;
- matching avançado;
- score ponderado;
- recomendações;
- analyzer;
- rotas da API.

---

## Build do Frontend

Para gerar a versão de produção do frontend:

```bash
cd frontend
npm run build
```

Para simular a versão final localmente:

```bash
npm run preview
```

---

## Estrutura do Projeto

```text
ai-resume-analyzer/
│
├── README.md
├── .gitignore
├── .python-version
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── analyzer.py
│   │   ├── matcher.py
│   │   ├── parser.py
│   │   ├── recommender.py
│   │   ├── schemas.py
│   │   ├── scorer.py
│   │   └── skills.py
│   │
│   └── tests/
│       ├── test_analyzer.py
│       ├── test_health.py
│       ├── test_matcher.py
│       ├── test_parser.py
│       ├── test_recommender.py
│       ├── test_routes.py
│       ├── test_scorer.py
│       └── test_skills.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── api.js
        ├── main.jsx
        ├── styles.css
        └── components/
            ├── InsightsPanel.jsx
            ├── Recommendations.jsx
            ├── ScoreCard.jsx
            ├── SkillsPanel.jsx
            └── UploadForm.jsx
```

---

## API

### `GET /health`

Verifica se a API está funcionando.

Resposta:

```json
{
  "status": "ok"
}
```

---

### `POST /analyze`

Analisa o currículo com base na descrição da vaga.

Campos enviados via `multipart/form-data`:

| Campo | Tipo | Descrição |
|---|---|---|
| file | PDF | Currículo do usuário |
| job_description | string | Descrição da vaga |

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

---

## Deploy

O projeto está publicado com:

- backend no Render;
- frontend na Vercel.

### Backend

```text
https://ai-resume-analyzer-wh05.onrender.com
```

### Frontend

```text
https://ai-resume-analyzer-app-pi.vercel.app
```

### Documentação da API

```text
https://ai-resume-analyzer-wh05.onrender.com/docs
```

---

## Roadmap

Possíveis melhorias futuras:

- adicionar camada de IA para feedback textual;
- gerar sugestões de reescrita do currículo;
- gerar carta de apresentação;
- adicionar OCR para PDFs escaneados;
- suportar DOCX;
- permitir comparação com múltiplas vagas;
- salvar histórico de análises;
- exportar resultado em PDF;
- criar autenticação;
- adicionar dashboard de evolução do candidato.

---

## Possível Evolução com IA

A arquitetura atual foi pensada para permitir a adição de IA no futuro.

A ideia não é substituir a lógica determinística, mas complementar a análise.

Exemplo de evolução:

```text
Currículo + vaga
        ↓
Motor determinístico gera dados estruturados
        ↓
IA transforma esses dados em feedback natural
        ↓
Usuário recebe sugestões mais personalizadas
```

A IA poderia ser usada para:

- explicar melhor os gaps;
- sugerir frases para o currículo;
- adaptar o resumo profissional;
- melhorar descrições de experiências;
- criar cartas de apresentação personalizadas.

---

## Contribuição

Contribuições são bem-vindas.

Fluxo sugerido:

```bash
git checkout -b feature/minha-feature
git commit -m "feat: adiciona minha feature"
git push origin feature/minha-feature
```

Depois, abra um Pull Request.

---

## Licença

Este projeto está sob a licença MIT.

---

## Autoria

Desenvolvido como projeto de portfólio com foco em:

- Python;
- FastAPI;
- React;
- APIs modernas;
- frontend responsivo;
- testes automatizados;
- análise determinística de currículos e vagas.

O projeto demonstra a construção de uma aplicação full-stack completa, com backend, frontend, deploy, testes e lógica de análise explicável.
