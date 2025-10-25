from langchain_chroma import Chroma  # type: ignore

from src.llm.embedding.config import embeddings

vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",
)
