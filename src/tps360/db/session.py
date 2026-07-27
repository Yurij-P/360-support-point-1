from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from tps360.db.engine import engine

SessionLocal = sessionmaker[Session](bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
