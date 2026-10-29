from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TaskCreate, TaskRead, TaskUpdate
from app.services import create_task, delete_task, get_task, list_tasks, replace_task

router = APIRouter(tags=["tasks"])

_NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Aucune tâche ne porte cet identifiant.",
        "content": {
            "application/json": {"example": {"detail": "Tâche introuvable"}}
        },
    }
}

_PRIORITY_ERROR = {
    "detail": [
        {
            "type": "enum",
            "loc": ["body", "priority"],
            "msg": "Input should be 'low', 'medium' or 'high'",
            "input": "urgent",
            "ctx": {"expected": "'low', 'medium' or 'high'"},
        }
    ]
}

_ID_ERROR = {
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["path", "task_id"],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "abc",
        }
    ]
}

_INVALID_BODY = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": (
            "Titre vide, titre de plus de 100 caractères, "
            "ou priorité autre que low, medium ou high."
        ),
        "content": {"application/json": {"example": _PRIORITY_ERROR}},
    }
}

_INVALID_ID = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "L'identifiant n'est pas un entier.",
        "content": {"application/json": {"example": _ID_ERROR}},
    }
}

_INVALID_BODY_OR_ID = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": (
            "Titre vide, titre de plus de 100 caractères, "
            "priorité autre que low, medium ou high, "
            "ou identifiant qui n'est pas un entier."
        ),
        "content": {
            "application/json": {
                "examples": {
                    "priorite": {
                        "summary": "Priorité inconnue",
                        "value": _PRIORITY_ERROR,
                    },
                    "identifiant": {
                        "summary": "Identifiant non entier",
                        "value": _ID_ERROR,
                    },
                }
            }
        },
    }
}

_CREATE_EXAMPLES = {
    "nouvelle": {
        "summary": "Nouvelle tâche",
        "description": "done peut être omis : il vaut alors false.",
        "value": {
            "title": "Apprendre FastAPI",
            "done": False,
            "priority": "medium",
        },
    }
}

_UPDATE_EXAMPLES = {
    "remplacement": {
        "summary": "Tâche terminée",
        "description": "title, done et priority sont tous présents.",
        "value": {
            "title": "Apprendre FastAPI",
            "done": True,
            "priority": "medium",
        },
    }
}


@router.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une tâche",
    description=(
        "Enregistre une tâche. Le titre contient de 1 à 100 caractères. "
        "done vaut false s'il est omis. priority vaut low, medium ou high."
    ),
    responses=_INVALID_BODY,
)
def create(
    data: TaskCreate = Body(openapi_examples=_CREATE_EXAMPLES),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    return create_task(db, current_user.id, data)


@router.get(
    "/tasks",
    response_model=List[TaskRead],
    summary="Lister les tâches",
    description=(
        "Retourne une page de tâches, triées par identifiant croissant. "
        "skip et limit découpent la page. done filtre les tâches terminées ou non."
    ),
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre de tâches à ignorer."),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Nombre maximum de tâches renvoyées.",
    ),
    done: Optional[bool] = Query(
        None,
        description="Filtre sur l'état. Absent : toutes les tâches.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TaskRead]:
    return list_tasks(db, current_user.id, skip, limit, done)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Lire une tâche",
    description="Retourne la tâche dont l'identifiant est dans l'URL.",
    responses={**_NOT_FOUND, **_INVALID_ID},
)
def read_one(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task = get_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    return task


@router.put(
    "/tasks/{task_id}",
    response_model=TaskRead,
    summary="Remplacer une tâche",
    description=(
        "Remplace le titre, l'état et la priorité. "
        "Les trois champs sont obligatoires."
    ),
    responses={**_NOT_FOUND, **_INVALID_BODY_OR_ID},
)
def replace(
    task_id: int,
    data: TaskUpdate = Body(openapi_examples=_UPDATE_EXAMPLES),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task = replace_task(db, current_user.id, task_id, data)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une tâche",
    description="Supprime la tâche et ne renvoie pas de corps.",
    responses={**_NOT_FOUND, **_INVALID_ID},
)
def remove(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    task = delete_task(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
