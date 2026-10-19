from pathlib import Path
from tqdm import tqdm
import numpy as np
import argparse

from src.recommenders.data import (
    RecommenderData,
    load_cached_recommender_data,
)
from src.recommenders.user_cf import recommend
from src.recommenders.als import ExplicitALS
from src.evaluation.metrics import precision_at_k, recall_at_k, ndcg_at_k
from src.evaluation.split import split_users_ratings


CACHE_DIR = Path("artifacts/recommender")

N_USERS = 50
MIN_USER_RATINGS = 100

TEST_SIZE = 0.2
RANDOM_SEED = 42

TOP_K = 20
LIKE_THRESHOLD = 8.0


def recommend_popular(
    data:RecommenderData,
    username: str,
    top_k: int = 20
) -> set[int]: # TODO refacture could be problematic 
    user_idx = data.user_to_idx[username]

    popularity = np.diff(
        data.ratings.tocsc().indptr
    ).copy()

    watched_films = data.ratings[user_idx].indices

    popularity[watched_films] = -1

    top_indices = np.argsort(
        popularity 
    )[::-1][:top_k]

    return [
        int(idx)
        for idx in top_indices
        if popularity[idx] > 0
    ]

def evaluate_user(
    train_data: RecommenderData,
    user_idx: int,
    hidden_ratings: dict[int, float],
    recommender: str = "cf",
    als_model: ExplicitALS | None = None
) -> dict:

    username = str(train_data.users[user_idx])

    if recommender == "cf":
        recommendations = recommend(
            data=train_data,
            username=username,
            n_recommendations=TOP_K,
            n_neighbors=50,
            min_common_films=20,
            min_neighbor_ratings=3,
        )

        recommended_films = [
            train_data.film_to_idx[rec["film"]]
            for rec in recommendations
        ]

    elif recommender == "popular":
        recommended_films = recommend_popular(
            data=train_data,
            username=username,
            top_k=TOP_K,
        )

    elif recommender == "als":
        if als_model is None:
            raise ValueError("ALS model is not provided")

        recommended_films = als_model.recommend(
            user_idx=user_idx,
            ratings=train_data.ratings,
            n_recommendations=TOP_K
        )

    else:
        raise ValueError(
            f"Unknown recommender: {recommender}"
        )

    relevant_films = {
        film_idx
        for film_idx, rating in hidden_ratings.items()
        if rating >= LIKE_THRESHOLD
    }

    hits = len(
        set(recommended_films[:TOP_K]) & relevant_films
    )

    precision = precision_at_k(
        recommended_films,
        relevant_films,
        TOP_K,
    )

    recall = recall_at_k(
        recommended_films,
        relevant_films,
        TOP_K,
    )

    ndcg = ndcg_at_k(
        recommended_films,
        relevant_films,
        TOP_K,
    )

    return {
        "username": username,
        "hidden": len(hidden_ratings),
        "relevant": len(relevant_films),
        "hits": hits,
        "precision": precision,
        "recall": recall,
        "ndcg": ndcg,
    }

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Filmatch recommenders"
    )

    parser.add_argument(
        "--user",
        type=str,
        default=None,
        help="Evaluate a specific user",
    )

    parser.add_argument(
        "--n-users",
        type=int,
        default=N_USERS,
        help="Number of users to evaluate",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed",
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=TEST_SIZE,
        help="Fraction of ratings to hide",
    )

    parser.add_argument(
        "--model",
        choices=["cf", "popular", "als", "all"],
        default="all"
    )

    return parser.parse_args()

def main() -> None:
    args = parse_args()

    if args.n_users < 1:
        raise ValueError("--n-users must be positive")

    rng = np.random.default_rng(args.seed)

    data = load_cached_recommender_data(CACHE_DIR)

    models = (
        ["cf", "popular", "als"] if args.model == "all" else [args.model]
    )

    if args.user is not None:
        username = args.user.lower()

        if username not in data.user_to_idx:
            raise ValueError(
                f"Unknown user: {username}"
            )

        selected_users = np.array([
            data.user_to_idx[username]
        ])

    else:
        user_rating_counts = np.diff(
            data.ratings.indptr
        )

        eligible_users = np.flatnonzero(
            user_rating_counts >= MIN_USER_RATINGS
        )

        selected_users = rng.choice(
            eligible_users,
            size=min(args.n_users, len(eligible_users)),
            replace=False,
        )

    train_data, hidden_by_user = split_users_ratings(
        data=data,
        user_indices=selected_users,
        rng=rng,
        test_size=args.test_size,
    )

    assert train_data.ratings.shape == data.ratings.shape

    for user_idx, hidden_ratings in hidden_by_user.items():
        hidden_films = np.array(
            list(hidden_ratings),
            dtype=np.int64,
        )

        assert train_data.ratings[
            user_idx, hidden_films
        ].nnz == 0

        assert (
            train_data.ratings[user_idx].nnz
            + len(hidden_ratings)
            == data.ratings[user_idx].nnz
        )

    print("Train/test split verified")

    als_model = None

    if "als" in models:
        print("Training ALS...")

        als_model = ExplicitALS(
            n_factors=32,
            regularization=10.0,
            n_iterations=20,
            random_seed=RANDOM_SEED
        )

        als_model.fit(train_data.ratings)

    results = {
        model: [] for model in models
    }

    for user_idx in tqdm(selected_users):
        user_idx = int(user_idx)

        hidden_ratings = hidden_by_user[user_idx]

        for recommender in results:
            result = evaluate_user(
                train_data=train_data,
                user_idx=user_idx,
                hidden_ratings=hidden_ratings,
                recommender=recommender,
                als_model=als_model
            )

            results[recommender].append(result)

            print()
            print(
                f"{result['username']:<25} "
                f"{recommender:<8} "
                f"hits={result['hits']:<3} "
                f"P@{TOP_K}={result['precision']:.3f} "
                f"R@{TOP_K}={result['recall']:.3f} "
                f"NDCG@{TOP_K}={result['ndcg']:.3f}"
            )

    print()
    print("AVERAGE RESULTS")
    print("=" * 75)

    for recommender, model_results in results.items():
        avg_precision = np.mean([
            result["precision"]
            for result in model_results
        ])

        recalls = np.array([
            result["recall"]
            for result in model_results
        ])

        avg_recall = (
            np.nanmean(recalls)
            if np.any(~np.isnan(recalls))
            else np.nan
        )

        ndcgs = np.array([
            result["ndcg"]
            for result in model_results
        ])

        avg_ndcg = (
            np.nanmean(ndcgs)
            if np.any(~np.isnan(ndcgs))
            else np.nan
        )

        print(
            f"{recommender:<10} "
            f"Precision@{TOP_K}={avg_precision:.4f} "
            f"Recall@{TOP_K}={avg_recall:.4f} "
            f"NDCG@{TOP_K}={avg_ndcg:.4f}"
        )


if __name__ == "__main__":
    main()
