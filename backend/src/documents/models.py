from pydantic import BaseModel


class FileModel(BaseModel):
    title: str
    text: str


class SearchWordModel(BaseModel):
    word: str
    frequency: int
    file_id: int
    idf: float
