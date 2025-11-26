from pydantic import BaseModel


class FileSnapshot(BaseModel):
    id: int
    hash_value: str
    path: str


class File(BaseModel):
    id: int
    hash_value: str
    path: str
    title: str
    text: str


class SearchWordModel(BaseModel):
    word: str
    frequency: int
    file_id: int
    idf: float
