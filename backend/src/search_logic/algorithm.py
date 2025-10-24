import math
from collections import Counter

from src.documents.models import SearchWordModel


def compute_tf_idf_vector(
    words_counter: Counter,
    word_idf_map: dict[str, float],
) -> dict[str, float]:
    """Вычисление TF-IDF вектора для документа или запроса"""
    vector = {}
    total_terms = sum(words_counter.values())

    for word, count in words_counter.items():
        if word in word_idf_map:
            tf = count / total_terms if total_terms > 0 else 0
            vector[word] = tf * word_idf_map[word]

    return vector


def cosine_similarity(
    doc_vector: dict[str, float],
    query_vector: dict[str, float],
) -> float:
    """Вычисление косинусной меры между вектором документа и запроса"""
    # Находим общие слова
    common_words = set(doc_vector.keys()) & set(query_vector.keys())

    if not common_words:
        return 0.0

    # Скалярное произведение
    dot_product = sum(
        doc_vector[word] * query_vector[word] for word in common_words
    )

    # Нормы векторов
    doc_norm = math.sqrt(sum(val**2 for val in doc_vector.values()))
    query_norm = math.sqrt(sum(val**2 for val in query_vector.values()))

    if doc_norm == 0 or query_norm == 0:
        return 0.0

    return dot_product / (doc_norm * query_norm)


def vector_search(
    query_words_counter: Counter,
    files: dict[int, list[SearchWordModel]],
) -> list[tuple[int, float]]:
    """Векторный поиск для всего запроса"""

    # Создаем карту IDF для всех слов в базе
    word_idf_map = {}
    for file_words in files.values():
        for word_data in file_words:
            if word_data.word not in word_idf_map:
                word_idf_map[word_data.word] = word_data.idf

    # Создаем TF-IDF вектор для запроса
    query_vector = compute_tf_idf_vector(query_words_counter, word_idf_map)

    # Если в запросе нет значимых слов, возвращаем пустой результат
    if not query_vector:
        return []

    # Вычисляем схожесть для каждого документа
    results = []

    for file_id, file_words in files.items():
        # Создаем TF-IDF вектор для документа
        doc_words_counter = Counter()
        for word_data in file_words:
            if word_data.frequency > 0:
                doc_words_counter[word_data.word] = word_data.frequency

        doc_vector = compute_tf_idf_vector(doc_words_counter, word_idf_map)

        # Вычисляем косинусную меру
        similarity = cosine_similarity(doc_vector, query_vector)

        if similarity > 0:
            results.append((file_id, similarity))

    # Сортируем по убыванию релевантности
    results.sort(key=lambda x: x[1], reverse=True)
    return results
