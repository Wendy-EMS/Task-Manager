from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.limiter import limiter
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router
from app.routers.tasks import router as tasks_router

app = FastAPI(
    title=settings.app_name,
    description=(
        "API de tâches : créer, lister, lire, remplacer et supprimer. "
        "Un jeton est exigé pour les tâches, et chaque compte ne voit que les siennes. "
        "Le titre est obligatoire et limité à 100 caractères. "
        "La priorité vaut low, medium ou high."
    ),
    openapi_tags=[
        {
            "name": "auth",
            "description": "Inscription et connexion.",
        },
        {
            "name": "tasks",
            "description": "Création, lecture, remplacement et suppression des tâches.",
        },
        {
            "name": "health",
            "description": "Disponibilité de l'API.",
        },
    ],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def hide_password_from_validation(request, exc):
    details = []
    for error in exc.errors():
        item = dict(error)
        if "password" in item.get("loc", ()):
            item.pop("input", None)
        details.append(item)
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(details)})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(health_router)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
