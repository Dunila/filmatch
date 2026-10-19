import numpy as np


def precision_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    hits = sum(
        film in relevant
        for film in recommended[:k]
    )

    return hits / k


def recall_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    if not relevant:
        return np.nan

    hits = sum(
        film in relevant
        for film in recommended[:k]
    )

    return hits / len(relevant)


def ndcg_at_k(
    recommended: list[int],
    relevant: set[int],
    k: int,
) -> float:
    if not relevant:
        return np.nan

    gains = np.array(
        [
            1.0 if film in relevant else 0.0
            for film in recommended[:k]
        ]
    )

    discounts = np.log2(
        np.arange(2, len(gains) + 2)
    )

    dcg = np.sum(gains / discounts)

    ideal_hits = min(len(relevant), k)

    ideal_discounts = np.log2(
        np.arange(2, ideal_hits + 2)
    )

    idcg = np.sum(1.0 / ideal_discounts)

    return float(dcg / idcg)