from fastapi import APIRouter


router = APIRouter(tags=["Healthcheck"])


@router.get("/ping")
async def ping():
    return "pong"
