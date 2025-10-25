from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2",
)

