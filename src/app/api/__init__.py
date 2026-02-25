from fastapi import APIRouter

from app.api.v1 import (
    login,
    verification_code,
    user,
)

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(verification_code.router)
api_router.include_router(user.router)
