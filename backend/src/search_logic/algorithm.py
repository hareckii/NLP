import math

from src.documents.models import WordWithIdfModel


def vector_search(
    query_word: str,
    files: dict[int, list[WordWithIdfModel]],
) -> list[tuple[int, float]]:
    idf_q = 0.0
    tf = 0.0
    # get idf and frequency for the query word
    for words_list in files.values():
        for word in words_list:
            if word.word == query_word:
                idf_q = word.idf
                tf = word.frequency
                break

    # compute similarities
    results: list[dict[int, float]] = []
    for file_id in files.keys():
        # compute the denominator (doc_norm = sqrt(sum (tf_t * idf_t)^2))
        sum_squares = 0.0
        for word in files[file_id]:
            if word.frequency > 0:
                val = word.frequency * word.idf
                sum_squares += val**2
        doc_norm = (
            math.sqrt(sum_squares) if sum_squares > 0 else 1.0
        )  # avoid division by zero

        # compute w for query_word: (tf * idf_q) / doc_norm
        w = (tf * idf_q) / doc_norm if doc_norm > 0 else 0.0
        sign = {"file_id": file_id, "value": w}
        results.append(sign)

    # sort by similarity descending
    results.sort(key=lambda x: x["value"], reverse=True)
    return results
