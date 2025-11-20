from fastapi import APIRouter

from app.check import Check

router = APIRouter()
checker = Check()


@router.get("/health")
def health_check():
    return {"status": checker.checking(), "service": "mindshipping"}


@router.get("/info")
def service_info():
    return {
        "service": "mindshipping",
        "message": "MindShipping backend placeholder endpoint",
    }
