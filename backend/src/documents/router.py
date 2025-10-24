from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.config import database
from src.db.models import FileModel, WordModel  # noqa: F401
from src.db.repositories.file_repo import FileRepository
from src.db.repositories.word_repo import WordRepository
from src.documents.file_processor import FileProcessor

router = APIRouter(prefix="/documents")


@router.delete("/reboot_db")
async def reboot_db():
    """Reboot DB(recreate it)"""
    await database.drop_tables()
    await database.create_tables()


@router.post("/add")
async def add_file(
    file: UploadFile,
    session: Annotated[AsyncSession, Depends(database.get_session)],
    title: str | None = None,
):
    # check txt format
    if not file.filename.endswith('.txt'):
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
    file_model = FileModel(title=file_title, text=content)
    file_model = await file_repo.add_file(file_model)

    # process file content
    # (return iterator with words and values of their frequency)
    processor = FileProcessor(file_model)
    words_counter = processor.process()
    words = words_counter.most_common()
    word_models = [
        WordModel(word=word[0], frequency=word[1], file_id=file_model.id)
        for word in words
        ]

    # add words into session
    word_repo = WordRepository(session)
    for word in word_models:
        await word_repo.add_word(word)


    return {'detail': "successfully add file"}


@router.delete("/delete")
async def delete_doc(title: str):
    pass
