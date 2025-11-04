from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

