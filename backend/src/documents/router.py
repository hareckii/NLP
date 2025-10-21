from fastapi import APIRouter

from src.db.config import database
from src.db.models import FileModel, WordModel  # noqa: F401

router = APIRouter(prefix="/documents")

@router.delete("/reboot_db")
async def reboot_db():
    """Reboot DB(recreate it)"""
    await database.drop_tables()
    await database.create_tables()


@router.post("/add")
async def add_doc(file_path: str, title: str):
    pass


@router.delete("/delete")
async def delete_doc(title: str):
    pass
