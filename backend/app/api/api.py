from fastapi import APIRouter
from app.api.routes import pdf_routes, biomarker_routes

router = APIRouter()

router.include_router(pdf_routes.router, prefix="/pdf", tags=["pdf"])
router.include_router(biomarker_routes.router, tags=["biomarkers"]) 