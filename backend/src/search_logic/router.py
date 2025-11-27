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



