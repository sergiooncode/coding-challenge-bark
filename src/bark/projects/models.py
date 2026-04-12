from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Integer, String, Boolean

from bark.projects.schemas import QuoteStatus
from bark.common.db import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    project_title = Column(String, nullable=False)
    category_id = Column(Integer, nullable=False)
    buyer_user_id = Column(Integer, nullable=False)
    response_cap = Column(Integer, nullable=False)
    response_count = Column(Integer, nullable=False)
    credits_required = Column(Integer, nullable=False)
    is_urgent = Column(Boolean, nullable=False)


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_id = Column(Integer, nullable=False)
    message = Column(String, nullable=False)
    price_cents = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default=QuoteStatus.pending)

    project_id = mapped_column(Integer, ForeignKey("projects.id"))

    __table_args__ = (
        UniqueConstraint("project_id", "seller_id"),
    )
