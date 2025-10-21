from fastapi import APIRouter

router = APIRouter(prefix="/search")


@router.get("/ask")
def search_document(message: str):
    pass
