from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FileModel, WordModel
from src.db.repositories.repo import Repository
from src.documents.models import FileSnapshot


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

    async def select_file(
        self,
        file_id: int,
    ) -> FileModel | None:
        query = select(FileModel).where(FileModel.id == file_id)
        res = await self.session.execute(query)
        return res.scalars().first()

    async def get_files_snapshot(self) -> list[FileSnapshot]:
        """
        Возвращает скриншот всех файлов в базе данных с хэшем и путями.

        Returns:
            Список классов с информацией о файлах
        """
        query = select(FileModel).order_by(FileModel.id)
        result = await self.session.execute(query)
        files = result.scalars().all()

        snapshot = [
            FileSnapshot(
                id=file.id,
                path=file.path,
                hash_value=file.hash_value,
            )
            for file in files
        ]

        return snapshot

    async def update_file_with_words(
        self,
        file: FileModel,
        new_words: list[WordModel],
    ) -> FileModel:
        """
        Обновляет файл и все связанные слова.
        """
        try:
            # 1. Удаляем старые слова этого файла - используем delete().where()
            delete_stmt = WordModel.__table__.delete().where(
                WordModel.file_id == file.id,
                )
            await self.session.execute(delete_stmt)

            # 2. Обновляем файл
            update_stmt = (
                update(FileModel)
                .where(FileModel.id == file.id)
                .values(
                    title=file.title,
                    text=file.text,
                    path=file.path,
                    hash_value=file.hash_value,
                )
            )
            await self.session.execute(update_stmt)

            # 3. Добавляем новые слова
            for word in new_words:
                word.file_id = file.id
                self.session.add(word)

            await self.session.flush()

            # 4. Возвращаем обновленный файл
            query = select(FileModel).where(FileModel.id == file.id)
            result = await self.session.execute(query)
            return result.scalar_one()

        except Exception as e:
            await self.session.rollback()
            raise e
    
    async def delete_file(
        self,
        file_id: int,
    ) -> bool:
        """
        Удаляет файл и все связанные слова.
        Returns:
            True если файл был удален, False если файл не найден
        """
        try:
            # Проверяем существование файла
            existing_file = await self.select_file(file_id)
            if not existing_file:
                return False

            # Удаляем связанные слова (каскадное удаление должно сработать автоматически)
            delete_words_stmt = WordModel.__table__.delete().where(
                WordModel.file_id == file_id
            )
            await self.session.execute(delete_words_stmt)

            # Удаляем файл
            delete_file_stmt = FileModel.__table__.delete().where(
                FileModel.id == file_id
            )
            result = await self.session.execute(delete_file_stmt)
            
            await self.session.flush()
            return True

        except Exception as e:
            await self.session.rollback()
            raise e
