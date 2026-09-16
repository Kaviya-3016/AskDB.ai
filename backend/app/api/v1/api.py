from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.schemas import router as schemas_router
from app.api.v1.queries import router as queries_router
from app.api.v1.results import router as results_router
from app.api.v1.admin import router as admin_router
from app.api.v1.health import router as health_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(schemas_router)
api_router.include_router(queries_router)
api_router.include_router(results_router)
api_router.include_router(admin_router)
api_router.include_router(health_router)
