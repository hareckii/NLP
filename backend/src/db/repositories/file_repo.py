from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FileModel
from src.db.repositories.repo import Repository


class FileRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def add_file(
        self,
        file: FileModel,
        ) -> FileModel:
        self.session.add(file)
        await self.session.flush()
        return file

    async def select_files(
        self,
        file_ids: list[int],
    ) -> list[FileModel]:
        query = select(FileModel).where(FileModel.id.in_(file_ids)).limit(10)
        res = await self.session.execute(query)
        return res.scalars().all()
