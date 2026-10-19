import numpy as np

from src.recommenders.data import RecommenderData


def split_users_ratings(
    data: RecommenderData,
    user_indices: np.ndarray,
    rng: np.random.Generator,
    test_size: float = 0.2,
) -> tuple[RecommenderData, dict[int, dict[int, float]]]:

    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    hidden_by_user = {}

    for user_idx in user_indices:
        user_idx = int(user_idx)

        user_ratings = data.ratings[user_idx]

        film_indices = user_ratings.indices
        ratings = user_ratings.data

        if len(film_indices) < 2:
            raise ValueError(
                f"User {user_idx} has fewer than 2 ratings"
            )

        n_test = min(
            len(film_indices) - 1,
            max(1, int(len(film_indices) * test_size)),
        )

        test_positions = rng.choice(
            len(film_indices),
            size=n_test,
            replace=False,
        )

        hidden_by_user[user_idx] = {
            int(film_indices[pos]): float(ratings[pos])
            for pos in test_positions
        }

    # Create one training matrix for all users.
    train_matrix = data.ratings.copy().tolil()

    for user_idx, hidden_ratings in hidden_by_user.items():
        train_matrix[
            user_idx, list(hidden_ratings)
        ] = 0

    train_matrix = train_matrix.tocsr()
    train_matrix.eliminate_zeros()

    train_data = RecommenderData(
        ratings=train_matrix,
        users=data.users,
        films=data.films,
        user_to_idx=data.user_to_idx,
        film_to_idx=data.film_to_idx,
    )

    return train_data, hidden_by_user
