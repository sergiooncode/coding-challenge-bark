import structlog
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bark.projects.models import Project, Quote as QuoteModel
from bark.projects.schemas import InputQuote as InputQuoteSchema, OutputQuote as OutputQuoteSchema, SortOrder, QuoteStatus
from bark.common.db import get_session

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/seller/barks/{project_id}/quotes", response_model=OutputQuoteSchema)
def create_quote(project_id: int, quote: InputQuoteSchema, db=Depends(get_session)):
    project = db.execute(
        select(Project).where(Project.id == project_id).with_for_update()
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Bark not found")

    if project.response_count >= project.response_cap:
        logger.warn("Bark already reach max response cap", count=project.response_count)
        raise HTTPException(status_code=400, detail="Bark already reach max response cap")

    existing_project_quote = db.query(QuoteModel).filter(
        QuoteModel.seller_id == quote.seller_id,
        QuoteModel.project_id == project_id
    ).first()
    if existing_project_quote:
        raise HTTPException(status_code=400, detail="Seller already has a quote for this bark")

    quote = QuoteModel(
        project_id=project_id,
        **quote.model_dump()
    )
    db.add(quote)

    project.response_count += 1
    db.add(project)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Seller already quoted this bark")
    db.refresh(quote)

    serialized_quote = OutputQuoteSchema.model_validate(quote)

    return serialized_quote


@router.get("/seller/barks/{project_id}")
def detail_bark(project_id: int, db=Depends(get_session)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Bark not found")
    return project


# It's namespaced by the actor's perspective. A seller seeing a bark gets
# credits_required, response_count, response_cap — fields relevant to deciding
# whether to respond. A buyer viewing the same project would see different
# data: quotes received, professional profiles, etc. Same underlying project,
# different API surface per role.
# This is actually a great detail to mention in the interview if it comes
# up — shows you think about API design from the consumer's perspective.
# Shall we resume?

@router.get("/buyer/projects/{project_id}/quotes")
def list_bark_quotes(project_id: int, db=Depends(get_session),
                     price_cents_sort: SortOrder = SortOrder.asc):
    project_quotes_query = db.query(QuoteModel).filter(
        QuoteModel.project_id == project_id
    )
    if price_cents_sort == "asc":
        project_quotes_query = project_quotes_query.order_by(QuoteModel.price_cents.asc())
    else:
        project_quotes_query = project_quotes_query.order_by(QuoteModel.price_cents.desc())
    project_quotes = project_quotes_query.all()

    quote_responses = [OutputQuoteSchema.model_validate(q) for q in project_quotes]

    return quote_responses


@router.post("/buyer/projects/{project_id}/quotes/{quote_id}/accept")
def accept_quote(project_id: int, quote_id: int, db=Depends(get_session)):
    existing_accepted_quotes = db.execute(
        select(QuoteModel).where(
            QuoteModel.project_id == project_id,
            QuoteModel.status == QuoteStatus.accepted
        ).with_for_update()
    ).scalars().all()
    if existing_accepted_quotes:
        raise HTTPException(status_code=400, detail="Project already has accepted quotes")

    quote_to_be_accepted = db.execute(
        select(QuoteModel).where(
            QuoteModel.id == quote_id
        ).where(
            QuoteModel.project_id == project_id
        ).with_for_update()
    ).scalar_one_or_none()

    if not quote_to_be_accepted:
        raise HTTPException(status_code=404, detail="Quote does not exist")

    quote_to_be_accepted.status = QuoteStatus.accepted
    db.add(quote_to_be_accepted)

    db.query(QuoteModel).filter(
        QuoteModel.project_id == project_id,
        QuoteModel.id != quote_id,
        QuoteModel.status == QuoteStatus.pending
    ).update({"status": QuoteStatus.rejected})

    db.commit()
    db.refresh(quote_to_be_accepted)

    serialized_quote = OutputQuoteSchema.model_validate(quote_to_be_accepted)

    return serialized_quote
