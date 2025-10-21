from fastapi import APIRouter

router = APIRouter(prefix="/llm")


@router.get("/ask")
def ask(message: str):
    pass
