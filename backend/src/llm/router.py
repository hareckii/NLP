from fastapi import APIRouter, File, HTTPException, status

from src.llm.vector_db.file_load import load_file

router = APIRouter(prefix="/llm")


@router.get("/ask")
def ask(message: str):
    pass

@router.post("/load_file")
def add_file(file: bytes = File(...)):
    content = file.decode()

    return load_file(text=content)
