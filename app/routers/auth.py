from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.schemas import Credentials, Token, UserRead
from app.security import create_access_token
from app.services.auth import authenticate, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte",
    description="Enregistre un email et le hash du mot de passe. Le mot de passe n'est pas renvoyé.",
)
def register(data: Credentials, db: Session = Depends(get_db)) -> UserRead:
    created = register_user(db, data)
    if created is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")
    return created


@router.post(
    "/login",
    response_model=Token,
    summary="Ouvrir une session",
    description="Vérifie le mot de passe et renvoie un jeton Bearer.",
)
@limiter.limit("5/minute")
def login(request: Request, data: Credentials, db: Session = Depends(get_db)) -> Token:
    user = authenticate(db, data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id), token_type="bearer")
