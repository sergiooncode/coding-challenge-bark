from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from bark.projects.routes import router
from bark.common.db import engine, Base, Session
from bark.projects.models import Project, Quote  # noqa

Base.metadata.create_all(engine)

session = Session()
initial_project = session.get(Project, 54134705)
if not initial_project:
    initial_project = Project(
        **{
            "id": 54134705,
            "project_title": "Web Development",
            "category_id": 1506,
            "buyer_user_id": 2147755,
            "response_cap": 5,
            "response_count": 0,
            "credits_required": 22,
            "is_urgent": False,
        }
    )
    session.add(initial_project)
    session.commit()

app = FastAPI()

app.include_router(router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )
