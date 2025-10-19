from fastapi import APIRouter


router = APIRouter(prefix="/documents")


@router.post("/add")
async def add_doc(file_path: str, title: str):
    pass

@router.delete("/delete")
async def delete_doc(title: str):
    pass