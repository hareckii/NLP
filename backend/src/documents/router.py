from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import database
from src.db.models import FileModel, WordModel  # noqa: F401
from src.db.repositories.file_repo import FileRepository
from src.db.repositories.word_repo import WordRepository
from src.documents.file_processor import FileProcessor
from src.documents.models import File
from src.search_logic.algorithm import vector_search

TAG = "Documents"

router = APIRouter(prefix="/documents", tags=[TAG])


@router.delete("/reboot_db")
async def reboot_db():
    """Reboot DB(recreate it)"""
    await database.drop_tables()
    await database.create_tables()


@router.post("/add")
async def add_file(
    title: Annotated[str, Form()],
    path: Annotated[str, Form()],
    hash_value: Annotated[str, Form()],
    file: UploadFile,
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    # check txt format
    if not file.filename.endswith(".txt"):
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="File must be *.txt",
        )

    # get file title and content
    byte_content = await file.read()
    content = byte_content.decode()
    file_title = title if title else file.filename

    # add file into session
    file_repo = FileRepository(session)
    file_model = FileModel(
        title=file_title,
        text=content,
        path=path,
        hash_value=hash_value,
    )
    file_model = await file_repo.add_file(file_model)

    # process file content
    # (return iterator with words and values of their frequency)
    processor = FileProcessor(file_model)
    words_counter = processor.get_words()
    words = words_counter.most_common()
    word_models = [
        WordModel(word=word[0], frequency=word[1], file_id=file_model.id)
        for word in words
    ]

    # add words into session
    word_repo = WordRepository(session)
    for word in word_models:
        await word_repo.add_word(word)

    return {"detail": "successfully add file"}


@router.get("/document")
async def get_document_by_id(
    id: int,
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    repo = FileRepository(session)
    res = await repo.select_file(id)
    return res


@router.delete("/delete/{file_id}")
async def delete_file_by_id(
    file_id: int,
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    """Удаляет файл по ID"""
    file_repo = FileRepository(session)
    
    success = await file_repo.delete_file(file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return {"detail": "File successfully deleted"}


@router.get("/snapshot")
async def get_snapshot(
    session: Annotated[AsyncSession, Depends(database.get_session)],
):
    repo = FileRepository(session)
    res = await repo.get_files_snapshot()
    return res


@router.patch("/update")
async def update_file(
    session: Annotated[AsyncSession, Depends(database.get_session)],
    file: File,
):
    file_repo = FileRepository(session)

    if await file_repo.select_file(file.id) is None:
        raise HTTPException(status_code=404, detail="Such file do not exists")
    # process file content
    # (return iterator with words and values of their frequency)
    file_model = FileModel(**file.model_dump())
    processor = FileProcessor(file_model)
    words_counter = processor.get_words()
    words = words_counter.most_common()
    word_models = [
        WordModel(word=word[0], frequency=word[1], file_id=file_model.id)
        for word in words
    ]
    # add file and words into session
    file_model = await file_repo.update_file_with_words(file_model, word_models)


    return {"detail": "successfully update file"}

@router.get("/search")
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
