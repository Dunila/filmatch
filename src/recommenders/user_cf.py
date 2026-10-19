import pandas as pd
import numpy as np
import sqlite3
import json
from tqdm import tqdm 
from scipy.sparse import csr_matrix

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
            target_centered, candidate_centered
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

    similar_users = find_similar_users_for_vector(
        data=data,
        target=target,
        n_neighbors=n_neighbors+1,
        min_common_films=min_common_films
    )

    return [
        user for user in similar_users if user["user_idx"] != target_idx
    ]

def find_similar_users_for_vector(
        data: RecommenderData,
        target: csr_matrix,
        n_neighbors: int = 50,
        min_common_films: int = 20
) -> list[dict]:
    target_films = target.indices
    common_counts = (
        data.ratings[:, target_films] != 0
    ).sum(axis=1)

    common_counts = np.asarray(common_counts).ravel()

    candidate_indices = np.flatnonzero(
        common_counts >= min_common_films
    )

    similar_users = []

    for user_idx in candidate_indices:
        candidate = data.ratings[user_idx]

        common_films = np.intersect1d(
            target.indices,
            candidate.indices
        )

        target_values = target[
            0, common_films
        ].toarray().ravel()

        candidate_values = candidate[
            0, common_films
        ].toarray().ravel()

        similarity = pearson_similarity(
            target_values,
            candidate_values
        )

        if similarity <= 0:
            continue

        similar_users.append({
            "user_idx": int(user_idx),
            "user": str(data.users[user_idx]),
            "similarity": float(similarity),
            "common_films": len(common_films)
        })

    similar_users.sort(
        key=lambda user: user["similarity"],
        reverse=True
    )

    return similar_users[:n_neighbors]

def recommend(
        data: RecommenderData,
        username: str,
        n_recommendations: int = 10,
        n_neighbors: int = 50,
        min_common_films: int = 20,
        min_neighbor_ratings: int = 3
) -> list[dict]:
    
    similar_users = find_similar_user(
        data=data,
        username=username,
        n_neighbors=n_neighbors,
        min_common_films=min_common_films
    )

    if not similar_users:
        return []

    target_idx = data.user_to_idx[username]
    target = data.ratings[target_idx]

    neighbor_indices = np.array(
        [user["user_idx"] for user in similar_users],
        dtype=np.int32
    )

    similarities = np.array(
        [user["similarity"] for user in similar_users],
        dtype=np.float32
    )

    neighbor_ratings = data.ratings[neighbor_indices]

    weighted_sum = (
        neighbor_ratings.T @ similarities
    )

    weighted_sum = np.asarray(weighted_sum).ravel()

    rated_mask = neighbor_ratings.copy()
    rated_mask.data[:] = 1

    similarity_sum = (
        rated_mask.T @ np.abs(similarities)
    )

    similarity_sum = np.asarray(
        similarity_sum
    ).ravel()

    rating_counts = np.asarray(
        rated_mask.sum(axis=0)
    ).ravel()

    predicted = np.zeros_like(
        weighted_sum,
        dtype=np.float32
    )

    valid = similarity_sum > 0

    predicted[valid] = (
        weighted_sum[valid] / similarity_sum[valid]
    )

    #Bayes smoothing like in IMDB see wiki Bayes_estimator Practical exaple of Bayes extimators
    target_values = target.data
    user_mean = float(np.mean(target_values))

    smoothing = 5.0

    predicted = (
        rating_counts * predicted + smoothing * user_mean
    ) / (rating_counts + smoothing)

    predicted[target.indices] = -np.inf

    predicted[
        rating_counts < min_neighbor_ratings
    ] = -np.inf

    valid_indices = np.flatnonzero(
        np.isfinite(predicted)
    )

    if valid_indices.size == 0:
        return []

    order = np.argsort(
        predicted[valid_indices]
    )[::-1]

    top_indices = valid_indices[
        order[:n_recommendations]
    ]

    return [
        {
            "film": data.films[film_idx],
            "predicted_rating": float(predicted[film_idx]),
            "neighbor_ratings": int(rating_counts[film_idx])
        }
        for film_idx in top_indices
    ]
    