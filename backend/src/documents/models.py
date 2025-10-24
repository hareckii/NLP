from pydantic import BaseModel


class FileModel(BaseModel):
    title: str
    text: str


class WordWithIdfModel(BaseModel):
    word: str
    frequency: int
    idf: float
