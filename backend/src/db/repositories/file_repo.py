from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FileModel


class FileRepository:

    async def add_file(
        title: str,
        text: str,
        session: AsyncSession,
        ) -> int:

        file = FileModel(title, text)
        session.add(file)
        await session.flush()
        return file.id
