from langchain.agents import create_agent
from langchain.tools import tool

from src.llm.ask_logic.model_config import llm
from src.llm.vector_db.config import vector_store


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=5)
    serialized = "\n\n".join(
        (f"Контекст: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

tools = [retrieve_context]
# If desired, specify custom instructions
prompt = """
    Ты помощник в системе поиска, отдаешь короткий ответ по базе знаний
    У тебя есть доступ к инструменту ретривера для системы поиска
    Используй инструмент для короткого ответа по запросу поиска
    Ответ должен быть не более 500 символов и основан только на контексте
    Если ты не уверен в ответе, отвечай: Нет короткого ответа.

    {agent_scratchpad}
    """

agent = create_agent(llm, tools, system_prompt=prompt)
