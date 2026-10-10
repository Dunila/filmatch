import sqlite3
from pathlib import Path
import numpy as np


DB_PATH = Path("data/parsed_data.db")

def fetch_one(
        conn: sqlite3.Connection,
        query: str
):
    #function to return one exact result
    result = conn.execute(query).fetchone()

    if result is None:
        return None

    return result[0]

def get_basic_stats(
        conn: sqlite3.Connection
) -> dict:
    #craete dict with basic stats - count of ratings, users, films in different tables
    return {
        "ratings_cnt": fetch_one(
            conn,
            "SELECT COUNT(*) FROM Ratings"
        ),
        "users_cnt": fetch_one(
            conn,
            "SELECT COUNT(*) FROM Users"
        ),
        "unique_users_in_ratings": fetch_one(
            conn,
            "SELECT COUNT(DISTINCT user) FROM Ratings"
        ),
        "unique_films_in_ratings": fetch_one(
            conn,
            "SELECT COUNT(DISTINCT film) FROM Ratings"
        )
    }

def get_duplicate_stats(
        conn: sqlite3.Connection
) -> dict:
    #print duplicate statistics
    duplicate_user_film_pairs = fetch_one(
        conn,
        """
        SELECT COUNT(*)
        FROM (
            SELECT user, film
            FROM Ratings
            GROUP BY user, film
            HAVING COUNT(*) > 1
        )
        """
    ) #Choose user-film pair that appears more than one time in rating and print count of such pairs

    duplicate_rating_rows = fetch_one(
        conn,
        """
        SELECT COALESCE(SUM(cnt - 1), 0)
        FROM (
            SELECT COUNT(*) AS cnt
            FROM Ratings
            GROUP BY user, film
            HAVING COUNT(*) > 1
        )
        """
    ) #Choose user-film pair that appears more than one time in rating and print SUM of count of such pairs

    duplicate_users = fetch_one(
        conn,
        """
        SELECT COUNT(*)
        FROM (
            SELECT username
            FROM Users
            GROUP BY username
            HAVING COUNT(*) > 1
        )
        """
    ) # print count of duplicates usernames in users

    duplicate_user_rows = fetch_one(
        conn,
        """
        SELECT COALESCE(SUM(cnt - 1), 0)
        FROM (
            SELECT COUNT(*) AS cnt
            FROM Users
            GROUP BY username
            HAVING COUNT(*) > 1
        )
        """
    ) 

    return {
        "duplicate_user_film_pairs": duplicate_user_film_pairs,
        "duplicate_rating_rows": duplicate_rating_rows,
        "duplicate_users": duplicate_users,
        "duplicate_user_rows": duplicate_user_rows
    }

def get_distribution_stats(
        conn: sqlite3.Connection,
        group_column: str
) -> dict:
    """Calculate dist of number of ratings grouped by user or film"""

    if group_column not in {"user", "film"}:
        raise ValueError(
            "group_column must be 'user' or 'film'"
        )

    query = f"""
        SELECT COUNT(*) AS cnt
        FROM Ratings
        GROUP BY {group_column}
    """

    counts = [
        row[0] for row in conn.execute(query).fetchall()
    ]

    if not counts:
        return {
            "min": 0,
            "median": 0,
            "mean": 0,
            "max": 0,
        }

    return {
        "min": float(np.min(counts)),
        "median": float(np.median(counts)),
        "mean": float(np.mean(counts)),
        "max": float(np.max(counts))
    }

def get_sparsity(
        ratings_cnt: int,
        users_cnt: int,
        films_cnt: int,
) -> float | None:
    """Calculate user-film matrix sparsity. Returns percentage of empty cells"""

    possible_interactions = users_cnt * films_cnt

    if possible_interactions == 0:
        return None

    density = ratings_cnt / possible_interactions

    return (1 - density) * 100

def print_distribution(
        title: str,
        stats: dict,
) -> None:
    print(f"\n{title}:")
    print(f"min: {stats['min']:,.1f}")
    print(f"median: {stats['median']:,.1f}")
    print(f"mean: {stats['mean']:,.1f}")
    print(f"max: {stats['max']:,.0f}")

def main() -> None:
    if not DB_PATH.exists():
        print(
            f"Database not found: \n{DB_PATH}"
        )
        return None

    print(f"Database: {DB_PATH}")
    print()
    with sqlite3.connect(DB_PATH) as conn:
        basic = get_basic_stats(conn)
        duplicates = get_duplicate_stats(conn)
        ratings_per_user_distr = get_distribution_stats(conn, "user")
        ratings_per_film_distr = get_distribution_stats(conn, "film")
    sparsity = get_sparsity(
        ratings_cnt=basic["ratings_cnt"],
        users_cnt=basic["unique_users_in_ratings"],
        films_cnt=basic["unique_films_in_ratings"]
    )

    print("_" * 50)
    print("\n Basic stats: ")

    print(f"\nRatings: {basic['ratings_cnt']:,} \n")
    print(f"\nUsers table: {basic['users_cnt']:,} \n")
    print(f"\nUnique users in Ratings: {basic['unique_users_in_ratings']:,} \n")
    print(f"\nUnique films in Ratings: {basic['unique_films_in_ratings']:,} \n")

    print("_" * 50)
    print("\n Duplicates stats: ")

    print(f"\n Duplicate user-film pairs: {duplicates['duplicate_user_film_pairs']:,}")
    print(f"\n Duplicate ratings: {duplicates['duplicate_rating_rows']:,}")
    print(f"\n Duplicate users: {duplicates['duplicate_users']:,}")
    print(f"\n Duplicate user rows: {duplicates['duplicate_user_rows']:,}")

    print("_" * 50)

    print_distribution(
        "Ratings per user",
        ratings_per_user_distr
    )

    print("_" * 50)

    print_distribution(
            "Ratings per film",
            ratings_per_film_distr
        )

    print("_" * 50)

    print("\n Matrix")

    if sparsity is not None:
        density = 100 - sparsity

        print(f" Density: {density:.6f}%")
        print(f"Sparsity: {sparsity:.6f}%")

    print()

if __name__ == "__main__":
    main()


