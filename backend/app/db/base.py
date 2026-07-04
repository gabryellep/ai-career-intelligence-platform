"""
base.py — Base declarativa do SQLAlchemy.

Todos os models de app/db/models.py herdam de Base. Também é o metadata
usado pelo Alembic (app/alembic/env.py) para autogeração de migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
