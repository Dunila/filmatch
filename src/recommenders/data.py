from dataclasses import dataclass
from pathlib import Path
import sqlite3

import numpy as np
from scipy.sparse import csr_matrix


@dataclass
class RecommenderData:
    ratings: csr_matrix
    users: np.ndarray
    films: np.ndarray
    user_to_idx: dict[str, int]
    film_to_idx: dict[str, int]

def load_users(
        conn: sqlite3.Connection
) -> np.ndarray:
    rows = conn.execute(
        """
        SELECT DISTINCT user
        FROM Ratings
        WHERE user IS NOT NULL
        ORDER BY user
        """
    )

    return np.array(
        [row[0] for row in rows], dtype=str
    )

def load_films(
        conn: sqlite3.Connection
) -> np.ndarray:
    
    rows = conn.execute(
        """
        SELECT DISTINCT film
        FROM Ratings
        WHERE film IS NOT NULL
        ORDER BY film
        """
    )

    return np.array(
        [row[0] for row in rows], dtype=str
    )

def build_ratings_matrix(
        conn: sqlite3.Connection,
        user_to_idx: dict[str, int],
        film_to_idx: dict[str, int],
        chunk_size: int = 500_000,
        chunk_max: int = 100
) -> csr_matrix:
    n_users = len(user_to_idx)
    n_films = len(film_to_idx)

    matrix = csr_matrix(
        (n_users, n_films),
        dtype=np.float32
    )

    cursor = conn.execute(
        """
        SELECT user, film, rating
        FROM Ratings
        WHERE rating IS NOT NULL
            AND user IS NOT NULL
            AND film IS NOT NULL
        """
    )

    chunk_processed = 0

    while True:
        rows = cursor.fetchmany(chunk_size)

        if not rows:
            break

        if chunk_processed == chunk_max:
            break

        row_indices = np.fromiter(
            (
                user_to_idx[user] for user, _, _ in rows
            ),
            dtype=np.int32,
            count=len(rows)
        )

        col_indices = np.fromiter(
            (
                film_to_idx[film] for _, film, _ in rows
            ),
            dtype=np.int32,
            count=len(rows)
        )

        values = np.fromiter(
            (
                rating for _, _, rating in rows
            ),
            dtype=np.float32,
            count=len(rows)
        )

        chunk_matrix = csr_matrix(
            (
                values,
                (row_indices, col_indices)
            ),
            shape=(n_users, n_films),
            dtype=np.float32
        )

        matrix += chunk_matrix

        chunk_processed += 1
    
    return matrix

def load_recommender_data(
        db_path: Path | str
) -> RecommenderData:
    with sqlite3.connect(db_path) as conn:
        print("Loading users...")
        users = load_users(conn)

        print("Loading films...")
        films = load_films(conn)

        print(
            f"Found {len(users):,} users \n and {len(films):,} films"
        )

        user_to_idx = {
            username: idx for idx, username in enumerate(users)
        }

        film_to_idx = {
            film: idx for idx, film in enumerate(films)
        }

        print("Building ratings matrix...")

        ratings = build_ratings_matrix(
            conn=conn,
            user_to_idx=user_to_idx,
            film_to_idx=film_to_idx
        )

    return RecommenderData(
        ratings=ratings,
        users=users,
        films=films,
        user_to_idx=user_to_idx,
        film_to_idx=film_to_idx
    )

