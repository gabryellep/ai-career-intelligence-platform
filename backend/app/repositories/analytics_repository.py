"""
analytics_repository.py — Queries de agregação para o dashboard de carreira
(SPEC 0006).

Separado de app/repositories/analysis_repository.py de propósito: agregação
(GROUP BY, funções agregadas) é uma responsabilidade distinta de CRUD/leitura
individual, e concentra aqui toda a lógica que o futuro dashboard vai
consumir, sem misturar com save_analysis/list_analyses/get_analysis_by_id.

Regra de privacidade: nenhuma função deste módulo seleciona colunas de
hash, PDF ou texto bruto — apenas score, skill_name, status e created_at.

Isolamento por sessão (SPEC 0009): todas as funções recebem session_id e
restringem as métricas apenas às análises daquela sessão. AnalysisSkill
não tem session_id próprio — o filtro nela é sempre aplicado via JOIN
com Analysis.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db.models import Analysis, AnalysisSkill

_SKILL_STATUSES = ("matched", "partial", "missing", "extra")


def get_summary(db: Session, session_id: UUID) -> dict:
    """
    Métricas agregadas da sessão informada: total de análises, score
    médio/melhor/pior, total de skills matched/missing, e as 5 skills
    mais faltantes.

    Com a sessão sem nenhuma análise, retorna valores neutros (0/0.0/[])
    em vez de levantar exceção ou retornar None.
    """
    totals_row = db.execute(
        select(
            func.count(Analysis.id),
            func.avg(Analysis.score),
            func.max(Analysis.score),
            func.min(Analysis.score),
        ).where(Analysis.session_id == session_id)
    ).one()
    total_analyses, average_score, best_score, worst_score = totals_row

    matched_count = db.execute(
        select(func.count())
        .select_from(AnalysisSkill)
        .join(Analysis, Analysis.id == AnalysisSkill.analysis_id)
        .where(AnalysisSkill.status == "matched", Analysis.session_id == session_id)
    ).scalar_one()
    missing_count = db.execute(
        select(func.count())
        .select_from(AnalysisSkill)
        .join(Analysis, Analysis.id == AnalysisSkill.analysis_id)
        .where(AnalysisSkill.status == "missing", Analysis.session_id == session_id)
    ).scalar_one()

    most_common_missing = db.execute(
        select(AnalysisSkill.skill_name, func.count().label("count"))
        .join(Analysis, Analysis.id == AnalysisSkill.analysis_id)
        .where(AnalysisSkill.status == "missing", Analysis.session_id == session_id)
        .group_by(AnalysisSkill.skill_name)
        .order_by(func.count().desc())
        .limit(5)
    ).all()

    return {
        "total_analyses": total_analyses or 0,
        "average_score": float(average_score) if average_score is not None else 0.0,
        "best_score": best_score if best_score is not None else 0,
        "worst_score": worst_score if worst_score is not None else 0,
        "total_matched_skills": matched_count or 0,
        "total_missing_skills": missing_count or 0,
        "most_common_missing_skills": [
            {"skill_name": row.skill_name, "count": row.count} for row in most_common_missing
        ],
    }


def get_skills_ranking(db: Session, session_id: UUID, status: str | None = None) -> list[dict]:
    """
    Ranking de skills da sessão informada, com contagem por status
    (matched/partial/missing/extra) e total. Se `status` for informado,
    filtra para skills com pelo menos uma ocorrência daquele status e
    ordena por essa contagem especificamente; caso contrário, ordena por
    total_count.
    """
    count_columns = {
        s: func.sum(case((AnalysisSkill.status == s, 1), else_=0)).label(f"{s}_count") for s in _SKILL_STATUSES
    }
    total_column = func.count().label("total_count")

    query = (
        select(
            AnalysisSkill.skill_name,
            *count_columns.values(),
            total_column,
        )
        .join(Analysis, Analysis.id == AnalysisSkill.analysis_id)
        .where(Analysis.session_id == session_id)
        .group_by(AnalysisSkill.skill_name)
    )

    if status is not None:
        query = query.having(count_columns[status] > 0).order_by(count_columns[status].desc())
    else:
        query = query.order_by(total_column.desc())

    rows = db.execute(query).all()

    return [
        {
            "skill_name": row.skill_name,
            "matched_count": row.matched_count,
            "partial_count": row.partial_count,
            "missing_count": row.missing_count,
            "extra_count": row.extra_count,
            "total_count": row.total_count,
        }
        for row in rows
    ]


def get_timeline(db: Session, session_id: UUID, days: int = 30) -> list[dict]:
    """
    Análises da sessão informada, agrupadas por dia (contagem e score
    médio), para os últimos `days` dias. Dias sem nenhuma análise não
    aparecem na lista (sem preenchimento de gaps nesta etapa — ver
    SPEC 0006, pendências).
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    day_column = func.date(Analysis.created_at).label("day")

    rows = db.execute(
        select(day_column, func.count().label("analyses_count"), func.avg(Analysis.score).label("average_score"))
        .where(Analysis.created_at >= since, Analysis.session_id == session_id)
        .group_by(day_column)
        .order_by(day_column.asc())
    ).all()

    return [
        {
            "date": row.day,
            "analyses_count": row.analyses_count,
            "average_score": float(row.average_score) if row.average_score is not None else 0.0,
        }
        for row in rows
    ]
