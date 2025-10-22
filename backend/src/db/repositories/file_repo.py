from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FileModel
from src.db.repositories.repo import Repository


class FileRepository(Repository):
    def __init__(self, session):
        super().__init__(session)

    async def add_file(
        title: str,
        text: str,
        session: AsyncSession,
        ) -> int:

        file = FileModel(title, text)
        session.add(file)
        await session.flush()
        return file.id
