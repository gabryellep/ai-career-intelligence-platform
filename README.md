# AI Resume Analyzer

> Analise a compatibilidade do seu currículo com qualquer vaga de emprego — de forma simples, rápida e explicável.

![Demo placeholder](https://via.placeholder.com/800x450.png?text=AI+Resume+Analyzer+—+Demo)

---

## Badges

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat&logo=vite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## Sobre o Projeto

O **AI Resume Analyzer** é uma aplicação web full-stack que permite ao usuário enviar um currículo em PDF e colar a descrição de uma vaga de emprego. O sistema analisa a compatibilidade entre os dois documentos e retorna:

- **Score de compatibilidade** (0–100) com barra de progresso visual
- **Skills encontradas** — presentes tanto no currículo quanto na vaga
- **Skills faltantes** — exigidas pela vaga mas ausentes no currículo
- **Recomendações** — sugestões simples e explicáveis de melhoria

A análise é baseada em um dicionário curado de skills técnicas (mais de 100 termos), extração com regex e cálculo de score explicável — sem uso de APIs pagas ou modelos de linguagem na versão atual.

---

## Funcionalidades

- Upload de currículo em PDF (até 5 MB)
- Extração automática de texto do PDF
- Campo para colar a descrição da vaga
- Extração de skills técnicas com word boundaries (evita falsos positivos)
- Score de compatibilidade com fórmula transparente
- Identificação de skills encontradas e faltantes
- Recomendações contextuais baseadas no score
- Interface React responsiva (desktop e mobile)
- API REST com FastAPI e documentação automática (`/docs`)

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Extração de PDF | PyMuPDF (fitz) |
| Validação | Pydantic v2 |
| Frontend | React 18, Vite 5 |
| Estilo | CSS puro (sem frameworks) |
| Testes | pytest, httpx |

---

## Instalação e Execução

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- npm 9+

---

### Backend

```bash
# 1. Entre na pasta do backend
cd backend

# 2. Crie e ative um ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o servidor
uvicorn main:app --reload
```

O backend estará disponível em: `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

---

### Frontend

```bash
# 1. Entre na pasta do frontend
cd frontend

# 2. Instale as dependências
npm install

# 3. Inicie o servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:5173`

---

### Executando os Testes

```bash
# A partir da pasta backend (com o venv ativado)
cd backend
pytest tests/ -v
```

---

## Estrutura do Projeto

```
ai-resume-analyzer/
│
├── README.md                    # Este arquivo
├── .gitignore
│
├── backend/
│   ├── requirements.txt         # Dependências Python fixadas
│   ├── main.py                  # Entrypoint FastAPI — rotas e CORS
│   └── app/
│       ├── __init__.py
│       ├── parser.py            # Extração de texto de PDF (PyMuPDF)
│       ├── skills.py            # Dicionário de skills + extração com regex
│       ├── scorer.py            # Cálculo de score de compatibilidade
│       ├── analyzer.py          # Orquestrador — único ponto de entrada
│       ├── recommender.py       # Geração de recomendações textuais
│       └── schemas.py           # Contratos Pydantic (AnalyzeResponse)
│
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js           # Configuração Vite + proxy para backend
    └── src/
        ├── App.jsx              # Componente raiz — estado global
        ├── main.jsx             # Entrypoint React
        ├── api.js               # Chamadas HTTP ao backend
        ├── styles.css           # Estilos globais
        └── components/
            ├── UploadForm.jsx   # Formulário de upload e textarea
            ├── ScoreCard.jsx    # Card de score com barra de progresso
            ├── SkillsPanel.jsx  # Painéis de skills encontradas/faltantes
            └── Recommendations.jsx  # Lista de recomendações
```

---

## Diferenciais

- Análise **100% explicável** — sem modelos black-box
- Pipeline modular pronto para integração com IA (LLMs)
- Interface responsiva com foco em UX
- Backend robusto com tratamento de erros e validações
- Arquitetura desacoplada (parser, skills, scorer, analyzer)

## Como Funciona

```
Usuário envia PDF + descrição da vaga
              ↓
     Backend extrai texto do PDF
              ↓
  Skills extraídas do currículo e da vaga
  (regex com word boundaries — sem falsos positivos)
              ↓
  Score = round(skills_em_comum / skills_da_vaga × 100)
              ↓
  Recomendações geradas com base nas skills faltantes
              ↓
     Frontend exibe resultado visual
```

**Limitação do score:** O score considera apenas a presença de skills e não leva em conta nível de experiência, contexto ou relevância semântica. Esta é uma limitação intencional da v1, projetada para ser simples e explicável.

**Cobertura de skills:** A v1 foca em hard skills técnicas (linguagens, frameworks, ferramentas, cloud, dados/IA) com suporte básico a idiomas (inglês, espanhol, francês, alemão, mandarim, japonês). A detecção de idiomas é feita por presença de termos e variações ortográficas — sem análise semântica de nível de proficiência (ex: B2, fluente, avançado são detectados como presença do idioma, não como nível).

---

## Roadmap / Próximos Passos

A arquitetura modular do projeto foi projetada para permitir a adição de uma camada de IA generativa sem reescrita do código.

### Melhorias planejadas

- [ ] **Camada de LLM** — substituir o `recommender.py` por uma versão que chama um modelo de linguagem (OpenAI, Anthropic, ou modelo local via Ollama) para gerar feedback mais natural e personalizado
- [ ] **Feedback detalhado** — análise semântica do currículo com sugestões de melhoria de texto
- [ ] **Adaptação de currículo** — reescrever seções do currículo para se adequar melhor à vaga
- [ ] **Carta de apresentação** — geração automática baseada no currículo e na vaga
- [ ] **Explicação de gaps** — análise detalhada de por que certas skills são importantes para a vaga
- [ ] **Histórico de análises** — salvar e comparar análises anteriores
- [ ] **Suporte a múltiplos formatos** — DOCX, TXT além de PDF
- [ ] **OCR** — suporte a PDFs baseados em imagem

### Dependências futuras (não instaladas na v1)

```
openai      # API OpenAI / compatível com Ollama
langchain   # Orquestração de LLM
anthropic   # API Anthropic Claude
```

---

## Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do repositório
2. Crie uma branch para sua feature: `git checkout -b feature/minha-feature`
3. Faça commit das suas alterações: `git commit -m 'feat: adiciona minha feature'`
4. Faça push para a branch: `git push origin feature/minha-feature`
5. Abra um Pull Request

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

---

*Desenvolvido como projeto de portfólio para demonstrar integração de Python, FastAPI, React e técnicas de NLP aplicadas.*
