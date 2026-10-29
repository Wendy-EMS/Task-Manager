from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Vérifier que l'API répond",
    description="Retourne un état simple, sans authentification.",
    responses={
        200: {
            "description": "L'API répond.",
            "content": {
                "application/json": {"example": {"status": "ok"}}
            },
        }
    },
)
def health():
    return {"status": "ok"}
