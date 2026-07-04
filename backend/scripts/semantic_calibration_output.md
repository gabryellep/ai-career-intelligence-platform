# Calibração do matching semântico — SPEC 0013

Modelo: `all-MiniLM-L6-v2` (sentence-transformers). Amostra: 27 pares positivos, 17 pares negativos.

Gerado localmente por `backend/scripts/semantic_calibration.py` — não faz parte do CI nem do deploy.

## Métricas por threshold candidato

| Threshold | TP | FN | FP | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.50 | 9 | 18 | 0 | 17 | 1.00 | 0.33 | 0.50 |
| 0.55 | 8 | 19 | 0 | 17 | 1.00 | 0.30 | 0.46 |
| 0.60 | 3 | 24 | 0 | 17 | 1.00 | 0.11 | 0.20 |
| 0.65 | 2 | 25 | 0 | 17 | 1.00 | 0.07 | 0.14 |
| 0.70 | 2 | 25 | 0 | 17 | 1.00 | 0.07 | 0.14 |

## Pares positivos (similaridade real)

| Skill da vaga | Skill do currículo | Similaridade |
|---|---|---|
| rest api | http api | 0.76 |
| linux | unix operating system | 0.76 |
| mongodb | nosql database | 0.64 |
| docker | containers | 0.60 |
| elasticsearch | search engine | 0.59 |
| tensorflow | deep learning framework | 0.59 |
| oauth | authentication protocol | 0.58 |
| typescript | typed javascript | 0.58 |
| aws | cloud computing | 0.52 |
| django | python web framework | 0.50 |
| postgresql | relational database | 0.49 |
| nlp | text processing | 0.49 |
| git | version control | 0.44 |
| kubernetes | container orchestration | 0.42 |
| numpy | numerical computing | 0.38 |
| websocket | real-time communication | 0.38 |
| machine learning | ml | 0.37 |
| microservices | distributed architecture | 0.37 |
| graphql | api query language | 0.35 |
| pytest | python testing | 0.33 |
| pandas | data analysis | 0.29 |
| fastapi | python api | 0.27 |
| react | frontend | 0.25 |
| terraform | infrastructure as code | 0.25 |
| jenkins | ci/cd automation | 0.22 |
| ci/cd | github actions | 0.12 |
| redis | in-memory cache | 0.07 |

## Pares negativos (similaridade real)

| Skill da vaga | Skill do currículo | Similaridade |
|---|---|---|
| java | javascript | 0.40 |
| python | excel | 0.39 |
| numpy | photoshop | 0.33 |
| c | c# | 0.32 |
| aws | photoshop | 0.27 |
| terraform | photoshop | 0.24 |
| sql | ux design | 0.24 |
| docker | ux design | 0.23 |
| linux | excel | 0.21 |
| redis | excel | 0.19 |
| graphql | ux design | 0.17 |
| css | database indexing | 0.15 |
| github actions | photoshop | 0.14 |
| kubernetes | photoshop | 0.13 |
| oauth | photoshop | 0.12 |
| mongodb | excel | 0.10 |
| react | postgresql | 0.01 |
