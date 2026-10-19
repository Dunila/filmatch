import numpy as np
from scipy.sparse import csr_matrix
from tqdm import trange


class ExplicitALS:
    def __init__(
            self,
            n_factors: int = 32,
            regularization: float = 10.0,
            n_iterations: int = 10,
            random_seed: int = 42
    ):
        self.n_factors = n_factors
        self.regularization = regularization
        self.n_iterations = n_iterations
        self.random_seed = random_seed

        self.user_factors = None
        self.item_factors = None

    def fit(self, ratings:csr_matrix) -> "ExplicitALS":
        ratings = ratings.tocsr()
        ratings_csc = ratings.tocsc()

        n_users, n_films = ratings.shape

        rng = np.random.default_rng(self.random_seed)

        self.user_factors = rng.normal(
            0, 0.1, size=(n_users, self.n_factors)
        ).astype(np.float32)

        self.item_factors = rng.normal(
            0, 0.1, size=(n_films, self.n_factors)
        ).astype(np.float32)

        identity = np.eye(
            self.n_factors, dtype=np.float32
        )

        for _ in trange(self.n_iterations, desc="ALS"):
            for user_idx in range(n_users):
                start = ratings.indptr[user_idx]
                end = ratings.indptr[user_idx+1]

                film_indices = ratings.indices[start:end]
                values = ratings.data[start:end]

                if len(film_indices) == 0:
                    continue

                Q = self.item_factors[film_indices]

                A = Q.T @ Q + self.regularization * identity
                b = Q.T @ values

                self.user_factors[user_idx] = np.linalg.solve(A, b)

            for film_idx in range(n_films):
                start = ratings_csc.indptr[film_idx]
                end = ratings_csc.indptr[film_idx+1]

                user_indices = ratings_csc.indices[start:end]
                values = ratings_csc.data[start:end]

                if len(user_indices) == 0:
                    continue

                P = self.user_factors[user_indices]

                A = P.T @ P + self.regularization * identity
                b = P.T @ values

                self.item_factors[film_idx] = np.linalg.solve(A, b)

        return self

    def predict(
            self,
            user_idx: int,
            film_idx: int
    ) -> float:
        if self.user_factors is None or self.item_factors is None:
            raise RuntimeError("Model is not fitted")

        return float(
            self.user_factors[user_idx] @ self.item_factors[film_idx]
        )

    def recommend(
            self,
            user_idx: int,
            ratings: csr_matrix,
            n_recommendations: int = 20
    ) -> list[int]:
        if self.user_factors is None or self.item_factors is None:
            raise RuntimeError("Model is not fitted")

        scores = self.item_factors @ self.user_factors[user_idx]

        watched_films = ratings[user_idx].indices
        scores[watched_films] = -np.inf

        item_counts = np.diff(ratings.tocsc().indptr)
        scores[item_counts < 1000] = -np.inf

        valid_indices = np.flatnonzero(np.isfinite(scores))

        order = np.argsort(scores[valid_indices])[::-1]

        return [
            int(idx) for idx in valid_indices[order[:n_recommendations]]
        ]