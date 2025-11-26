from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import database
from src.db.models import FileModel
from src.db.repositories.file_repo import FileRepository
from src.db.repositories.word_repo import WordRepository
from src.documents.file_processor import FileProcessor
from src.search_logic.algorithm import vector_search

router = APIRouter(prefix="/search")


@router.get("/ask")
async def search_document(
    message: str,
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    # process query
    file = FileModel(text=message)
    processor = FileProcessor(file)
    query_words_counter = processor.get_words()

    if not query_words_counter:
        raise HTTPException(
            status_code=404,
            detail="Do not find any matched files",
        )

    # get words with idf values
    word_repo = WordRepository(session)
    words = await word_repo.get_words_with_idf()
    # get files with search result
    search_results = vector_search(query_words_counter, words)

    # get all files
    file_repo = FileRepository(session)
    files_data = await file_repo.select_files(
        [file[0] for file in search_results],
    )
    similarities = [file[1] for file in search_results]

    # sort files
    order_mapping = {
        file_id: idx for idx, (file_id, _) in enumerate(search_results)
    }
    sorted_files = sorted(
        files_data,
        key=lambda x: order_mapping.get(x.id, float("inf")),
    )
    result_files = [
        {"id": file.id, "title": file.title, "similarity": similarities[i]}
        for i, file in enumerate(sorted_files)
    ]
    return result_files
