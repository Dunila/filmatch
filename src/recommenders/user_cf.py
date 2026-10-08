import pandas as pd
import numpy as np
import sqlite3
import json
from tqdm import tqdm 

from src.recommenders.data import RecommenderData


def get_common_counts(
        data: RecommenderData,
        user_idx: int
) -> np.ndarray:
    
    ratings = data.ratings
    target = ratings[user_idx]

    target_films = target.indices

    common_counts = (ratings[:, target_films] != 0).sum(axis=1)

    return np.asarray(common_counts).ravel() #ravel is like flatten

def pearson_similarity(
        target_ratings,
        candidate_ratings
) -> float:
    """Pearson correlation between ratings of two users"""

    target_ratings = np.asarray(
        target_ratings,
        dtype=np.float32
    )
    
    candidate_ratings = np.asarray(
        candidate_ratings,
        dtype=np.float32
    )

    target_centered = (
        target_ratings - target_ratings.mean()
    )

    candidate_centered = (
        candidate_ratings - candidate_ratings.mean()
    )

    denominator = (
        np.linalg.norm(target_centered) * np.linalg.norm(candidate_centered)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(
            target_ratings, candidate_centered
        ) / denominator
    )

def find_similar_user(
        data: RecommenderData,
        username: str,
        n_neighbors: int = 50,
        min_common_films: int = 10
) -> list[dict]:
    if username not in data.user_to_idx:
        raise ValueError(
            f"User '{username}' is not in ratings database"
        )

    target_idx = data.user_to_idx[username]
    target = data.ratings[target_idx]

    common_counts = get_common_counts(
        data=data,
        user_idx=target_idx
    )

    candidate_indices = np.flatnonzero(
        common_counts >= min_common_films
    )

    candidate_indices = candidate_indices[
        candidate_indices != target_idx
    ]

    similarities = []

    for candidate_idx in candidate_indices:
        candidate = data.ratings[candidate_idx]

        common_films = np.intersect1d(
            target.indices,
            candidate.indices,
            assume_unique=True
        )

        target_values = target[
            0,
            common_films
        ].toarray().ravel()

        candidate_values = candidate[
            0,
            common_films
        ].toarray().ravel()

        similarity = pearson_similarity(
            target_values,
            candidate_values
        )

        similarities.append(
            {
                "user": data.users[candidate_idx],
                "similarity": similarity,
                "common_films": len(common_films)
            }
        )

    similarities.sort(
        key = lambda row: row["similarity"],
        reverse=True
    )

    return similarities[:n_neighbors]

