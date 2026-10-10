from pathlib import Path

import numpy as np

from src.recommenders.data import (
    RecommenderData,
    load_cached_recommender_data,
)
from src.recommenders.user_cf import recommend


CACHE_DIR = Path("artifacts/recommender")

N_USERS = 5
MIN_USER_RATINGS = 100

TEST_SIZE = 0.2
RANDOM_SEED = 42

TOP_K = 20
LIKE_THRESHOLD = 8.0


def split_user_ratings(
    data: RecommenderData,
    user_idx: int,
    rng: np.random.Generator,
):
    """Hide 20% of the user's ratings."""

    user_ratings = data.ratings[user_idx]

    film_indices = user_ratings.indices
    ratings = user_ratings.data

    n_test = max(
        1,
        int(len(film_indices) * TEST_SIZE),
    )

    test_positions = rng.choice(
        len(film_indices),
        size=n_test,
        replace=False,
    )

    # Remember hidden films and their ratings.
    hidden_ratings = {
        int(film_indices[pos]): float(ratings[pos])
        for pos in test_positions
    }

    # Make an independent copy of the matrix.
    train_matrix = data.ratings.copy().tolil()

    # Remove hidden ratings from the target user's row.
    train_matrix[user_idx, list(hidden_ratings)] = 0

    train_matrix = train_matrix.tocsr()
    train_matrix.eliminate_zeros()

    train_data = RecommenderData(
        ratings=train_matrix,
        users=data.users,
        films=data.films,
        user_to_idx=data.user_to_idx,
        film_to_idx=data.film_to_idx,
    )

    return train_data, hidden_ratings

def recommend_popular(
    data:RecommenderData,
    username: str,
    top_k: int = 20
) -> set[int]:
    user_idx = data.user_to_idx[username]

    popularity = np.diff(
        data.ratings.tocsc().indptr
    ).copy()

    watched_films = data.ratings[user_idx].indices

    popularity[watched_films] = -1

    top_indices = np.argsort(
        popularity 
    )[::-1][:top_k]

    return set(
        int(idx) for idx in top_indices if popularity[idx] > 0
    )

def evaluate_user(
    data: RecommenderData,
    user_idx: int,
    rng: np.random.Generator,
    recommender: str = "cf" #or popullar
) -> dict:
    """Evaluate recommendations for one user."""

    username = str(data.users[user_idx])

    train_data, hidden_ratings = split_user_ratings(
        data=data,
        user_idx=user_idx,
        rng=rng,
    )

    if recommender == "cf":
        recommendations = recommend(
            data=train_data,
            username=username,
            n_recommendations=TOP_K,
            n_neighbors=50,
            min_common_films=20,
            min_neighbor_ratings=3,
        )

        recommended_films = {
            data.film_to_idx[rec["film"]]
            for rec in recommendations
        }

    elif recommender == "popular":
        recommended_films = recommend_popular(
            data=train_data,
            username=username,
            top_k=TOP_K,
        )

    relevant_films = {
        film_idx
        for film_idx, rating in hidden_ratings.items()
        if rating >= LIKE_THRESHOLD
    }

    hits = len(recommended_films & relevant_films)

    precision = hits / TOP_K

    recall = (
        hits / len(relevant_films)
        if relevant_films
        else 0.0
    )

    return {
        "username": username,
        "hidden": len(hidden_ratings),
        "relevant": len(relevant_films),
        "hits": hits,
        "precision": precision,
        "recall": recall,
    }


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)

    data = load_cached_recommender_data(CACHE_DIR)

    user_rating_counts = np.diff(
        data.ratings.indptr
    )

    eligible_users = np.flatnonzero(
        user_rating_counts >= MIN_USER_RATINGS
    )

    selected_users = rng.choice(
        eligible_users,
        size=min(N_USERS, len(eligible_users)),
        replace=False,
    )

    results = []

    print()
    print("FILMATCH EVALUATION")
    print("=" * 75)

    for user_idx in selected_users:
        result = evaluate_user(
            data=data,
            user_idx=int(user_idx),
            rng=rng,
        )

        results.append(result)

        print(
            f"{result['username']:<25} "
            f"hidden={result['hidden']:<5} "
            f"relevant={result['relevant']:<5} "
            f"hits={result['hits']:<3} "
            f"P@20={result['precision']:.3f} "
            f"R@20={result['recall']:.3f}"
        )

    print()
    print("AVERAGE RESULTS")
    print("=" * 75)

    avg_precision = np.mean([
        result["precision"]
        for result in results
    ])

    avg_recall = np.mean([
        result["recall"]
        for result in results
    ])

    print(f"Precision@{TOP_K}: {avg_precision:.4f}")
    print(f"Recall@{TOP_K}:    {avg_recall:.4f}")


if __name__ == "__main__":
    main()