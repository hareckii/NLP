
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.config import Base


class FileModel(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(40))
    text: Mapped[str]

    words: Mapped[list["WordModel"]] = relationship(back_populates="file")


class WordModel(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(30))
    significance: Mapped[float]
    file_id: Mapped[int] = mapped_column(
        ForeignKey(
            "files.id",
            ondelete="CASCADE",
            ),
        )

    file: Mapped["FileModel"] = relationship(back_populates="words")
