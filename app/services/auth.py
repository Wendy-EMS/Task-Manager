from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import Credentials, UserRead
from app.security import DUMMY_PASSWORD_HASH, hash_password, verify_password


def register_user(db: Session, data: Credentials) -> Optional[UserRead]:
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        return None
    user = User(email=data.email, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(user)
    return UserRead(id=user.id, email=user.email)


def authenticate(db: Session, data: Credentials) -> Optional[User]:
    user = db.scalar(select(User).where(User.email == data.email))
    if user is None:
        verify_password(data.password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(data.password, user.password_hash):
        return None
    return user
