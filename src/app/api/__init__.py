from fastapi import APIRouter

from app.api.v1 import (
    login,
    verification_code,
    user,
    task,
    stage,
    lesson,
    story,
    settings,
)

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(verification_code.router)
api_router.include_router(user.router)
api_router.include_router(story.router)
api_router.include_router(stage.router)
api_router.include_router(lesson.router)
api_router.include_router(task.router)
api_router.include_router(settings.router)
