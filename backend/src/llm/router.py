from fastapi import APIRouter, File

from src.llm.ask_logic.agent import agent
from src.llm.vector_db.file_load import load_file

router = APIRouter(prefix="/llm")


@router.get("/ask")
def ask(message: str):
    try:
        res = agent.invoke(
            stream_mode="values",
            input={"messages": [{"role": "user",
                "content": message}]})
        print(res["messages"])
        return res["messages"][-1].content
    except Exception as e:
        print(f"Ошибка LLM: {e}")

@router.post("/load_file")
def add_file(file: bytes = File(...)):
    content = file.decode()

    return load_file(text=content)
