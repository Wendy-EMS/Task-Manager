from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool = False
    priority: Priority

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Apprendre FastAPI",
                    "done": False,
                    "priority": "medium",
                }
            ]
        }
    )


class TaskUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    done: bool
    priority: Priority

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Apprendre FastAPI",
                    "done": True,
                    "priority": "medium",
                }
            ]
        }
    )


class TaskRead(BaseModel):
    id: int
    title: str = Field(min_length=1, max_length=100)
    done: bool
    priority: Priority

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "title": "Apprendre FastAPI",
                    "done": False,
                    "priority": "medium",
                }
            ]
        }
    )
