import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

_engine_options = {}
if settings.database_url.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}
else:
    _engine_options["pool_pre_ping"] = True
    # Le pooler de Neon (PgBouncer en mode transaction) refuse les requêtes préparées.
    _engine_options["connect_args"] = {"prepare_threshold": None}
    if os.environ.get("VERCEL"):
        _engine_options["poolclass"] = NullPool

engine = create_engine(settings.database_url, **_engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
