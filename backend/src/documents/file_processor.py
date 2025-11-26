from collections import Counter

from natasha import (
    Doc,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    NewsSyntaxParser,
    Segmenter,
)

from src.db.models import FileModel


class FileProcessor:
    def __init__(self, file: FileModel):
        self.segmenter = Segmenter()
        self.morph_vocab = MorphVocab()
        self.embedding = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(NewsEmbedding())
        self.syntax_parser = NewsSyntaxParser(self.embedding)
        self.ner_tagger = NewsNERTagger(self.embedding)

        self.file: FileModel = file

    def get_words(self) -> Counter:
        doc: Doc = Doc(self.file.text)
        doc.segment(self.segmenter)

        doc.tag_morph(self.morph_tagger)

        # части речи, которые не надо учитывать
        exclude_pos = {
            "PUNCT",
            "CONJ",
            "ADP",
            "PART",
            "SCONJ",
        }  # знаки препинания, союзы, предлоги, частицы

        lemmas = []
        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)

            # скип ненужного
            if token.pos in exclude_pos:
                continue

            lemmas.append(token.lemma)

        return Counter(lemmas)
