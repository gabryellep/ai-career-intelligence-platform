# Validação semântica real — SPEC 0012

Modelo: `all-MiniLM-L6-v2` (sentence-transformers). Threshold: `0.7`.

Gerado localmente por `backend/scripts/semantic_demo.py` — não faz parte do CI nem do deploy.

## Pares de skills

| Skill da vaga | Skill do currículo | Similaridade | Acima do threshold | Observação |
|---|---|---|---|---|
| docker | containers | 0.6 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| postgresql | relational database | 0.49 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| fastapi | python api | 0.27 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| nlp | text processing | 0.49 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| react | frontend | 0.25 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| ci/cd | github actions | 0.12 | não | Aproximação esperada NÃO confirmada — similaridade abaixo do threshold (0.7). Limitação real do modelo para este par. |
| react | postgresql | 0.01 | não | Falso positivo evitado — corretamente abaixo do threshold (0.7). |
| docker | ux design | 0.23 | não | Falso positivo evitado — corretamente abaixo do threshold (0.7). |
| python | excel | 0.39 | não | Falso positivo evitado — corretamente abaixo do threshold (0.7). |

## Cenário antes/depois

- Skills do currículo (sintéticas): python, containers, relational database, github actions
- Skills da vaga (sintéticas): python, docker, postgresql, ci/cd, aws
- `score` (determinístico): 20
- `semantic_score`: 20
- `hybrid_score`: 20
- `semantic_matches`:
  - (nenhum)
