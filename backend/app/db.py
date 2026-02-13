from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./data/metadata.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Atgriež DB sesiju; automātiski aizver pēc pieprasījuma."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Izveido visas tabulas, ja tās vēl neeksistē."""
    from app import models  # noqa: F401 — importē, lai reģistrētu modeļus

    Base.metadata.create_all(bind=engine)