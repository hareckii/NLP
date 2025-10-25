from langchain_classic.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.llm.vector_db.config import vector_store


def load_file(text: str):
    """Загрузка текстовых файлов и разбиение на чанки"""
    doc = Document(page_content=text)

    # Разбиение текста на чанки
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
    )

    chunks = text_splitter.split_documents([doc])
    vector_store.add_documents(chunks)
    return chunks
