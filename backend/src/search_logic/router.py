from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import database
from src.db.repositories.file_repo import FileRepository
from src.db.repositories.word_repo import WordRepository
from src.search_logic.algorithm import vector_search

router = APIRouter(prefix="/search")


@router.get("/ask")
async def search_document(
    message: str,
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    # get words with idf value grouped by file id
    word_repo = WordRepository(session)
    files = await word_repo.get_words_with_log_nf()

    # compute significance by vector search
    significances = vector_search(message, files)
    print(f"{significances=}")
    file_ids = [sign["file_id"] for sign in significances if sign["value"] > 0]
    file_repo = FileRepository(session)
    res = await file_repo.select_files(file_ids)

    # sort selected values
    order_mapping = {
        item: index for index, item in enumerate(file_ids)
    }

    return sorted(res, key=lambda x: order_mapping[x.id])
