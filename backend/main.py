from fastapi import FastAPI, status
from src import search_router, llm_router, documents_router

app = FastAPI()

app.include_router(search_router)
app.include_router(llm_router)
app.include_router(documents_router)


@app.get("/is_healthy", status_code=status.HTTP_200_OK)
def health_check():
    return "OK"
