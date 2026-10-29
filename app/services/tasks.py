from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Task
from app.schemas import Priority, TaskCreate, TaskRead, TaskUpdate


def _to_read(task: Task) -> TaskRead:
    return TaskRead(
        id=task.id,
        title=task.title,
        done=task.done,
        priority=Priority(task.priority),
    )


def _owned_task(db: Session, user_id: int, task_id: int) -> Optional[Task]:
    return db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))


def create_task(db: Session, user_id: int, data: TaskCreate) -> TaskRead:
    task = Task(
        title=data.title,
        done=data.done,
        priority=data.priority.value,
        user_id=user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _to_read(task)


def list_tasks(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
    done: Optional[bool],
) -> List[TaskRead]:
    query = select(Task).where(Task.user_id == user_id).order_by(Task.id)
    if done is not None:
        query = query.where(Task.done.is_(done))
    rows = db.scalars(query.offset(skip).limit(limit)).all()
    return [_to_read(row) for row in rows]


def get_task(db: Session, user_id: int, task_id: int) -> Optional[TaskRead]:
    task = _owned_task(db, user_id, task_id)
    if task is None:
        return None
    return _to_read(task)


def replace_task(
    db: Session,
    user_id: int,
    task_id: int,
    data: TaskUpdate,
) -> Optional[TaskRead]:
    task = _owned_task(db, user_id, task_id)
    if task is None:
        return None
    task.title = data.title
    task.done = data.done
    task.priority = data.priority.value
    db.commit()
    db.refresh(task)
    return _to_read(task)


def delete_task(db: Session, user_id: int, task_id: int) -> Optional[TaskRead]:
    task = _owned_task(db, user_id, task_id)
    if task is None:
        return None
    read = _to_read(task)
    db.delete(task)
    db.commit()
    return read
