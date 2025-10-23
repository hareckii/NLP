from pydantic import BaseModel


class FileModel(BaseModel):
    title: str
    text: str


class WordModel(BaseModel):
    word: str
    frequency: int
