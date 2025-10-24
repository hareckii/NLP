import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import FileModel, WordModel
from src.db.repositories.repo import Repository
from src.documents.models import WordWithIdfModel


class WordRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def add_word(
        self,
        word: WordModel,
    ) -> None:
        self.session.add(word)

    async def get_words_with_log_nf(self) -> dict[int, list[WordWithIdfModel]]:
        """get value log(n/pi) for every word,
        group by file_id

        Returns:
            dict[int, list[WordWithIdfModel]]: file_id: words
        """
        # get number of all docs
        total_docs_query = select(func.count(FileModel.id))
        total_docs_result = await self.session.execute(total_docs_query)
        total_docs = total_docs_result.scalar() or 1

        # get number of docs for every word(where it exists)
        word_doc_counts_query = select(
            WordModel.word,
            func.count(func.distinct(WordModel.file_id)).label("doc_count"),
        ).group_by(WordModel.word)

        word_doc_counts_result = await self.session.execute(
            word_doc_counts_query,
        )

        word_doc_counts = {
            row.word: row.doc_count for row in word_doc_counts_result
        }

        # get all words group by file_id
        words_by_file_query = select(WordModel).order_by(WordModel.file_id)
        words_result = await self.session.execute(words_by_file_query)
        all_words = words_result.scalars().all()

        # compute idf for all words
        results = {}
        for word_model in all_words:
            file_id = word_model.file_id
            doc_count = word_doc_counts.get(word_model.word, 0)

            if file_id not in results:
                results[file_id] = []

            if doc_count > 0:
                log_nf = math.log(total_docs / doc_count)
                word_with_idf = WordWithIdfModel(
                    word=word_model.word,
                    frequency=word_model.frequency,
                    file_id=file_id,
                    idf=float(log_nf),
                )
                results[file_id].append(word_with_idf)

        return results
