from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///bark.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()


def get_session() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    with Session() as session:
        yield session
