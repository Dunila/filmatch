from pathlib import Path
import sqlite3

import pandas as pd


DEFAULT_DB_PATH = Path("data/parsed_data.db")



def connect(
    db_path = DEFAULT_DB_PATH,
) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def initialize_db(
    db_path = DEFAULT_DB_PATH,
) -> None:
    """
    Create database and tables if they do not exist.
    Existing tables and data are not modified.
    """

    db_path = Path(db_path)

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    query = """
    CREATE TABLE IF NOT EXISTS Ratings (
        user TEXT,
        liked INTEGER,
        film TEXT,
        reviewed INTEGER,
        rating INTEGER
    );

    CREATE TABLE IF NOT EXISTS Users (
        username TEXT,
        status TEXT,
        display_name TEXT,
        geo TEXT,
        films INTEGER,
        thisyear INTEGER,
        lists INTEGER,
        following INTEGER,
        followers INTEGER,
        favorities TEXT
    );
    """

    with connect(db_path) as conn:
        conn.executescript(query)


def load_ratings(
    db_path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """
    load ratings table ()
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM Ratings",
            conn,
        )


def load_users(
    db_path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """
    load users table ()
    """
    with connect(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM Users",
            conn,
        )


def count_ratings(
    db_path = DEFAULT_DB_PATH,
) -> int:
    """
    Display count of ratings in db
    """
    with connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM Ratings"
        )

        return cursor.fetchone()[0]


def count_users(
    db_path = DEFAULT_DB_PATH,
) -> int:
    """
    Display count of users in db
    """
    with connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM Users"
        )

        return cursor.fetchone()[0]


def count_films(
    db_path = DEFAULT_DB_PATH,
) -> int:
    """
    Display count of unique films in database
    """
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT COUNT(DISTINCT film)
            FROM Ratings
            """
        )

        return cursor.fetchone()[0]


def insert_user(
    conn,
    user,
) -> None:
    """
    Insert one user using an existing database connection.

    Does NOT commit the transaction.
    """

    query = """
    INSERT INTO Users (
        username,
        status,
        display_name,
        geo,
        films,
        thisyear,
        lists,
        following,
        followers,
        favorities
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    geo = user.get("geo")

    if isinstance(geo, list):
        geo = ", ".join(geo)

    favorites = user.get("favorities")

    if isinstance(favorites, list):
        favorites = ", ".join(favorites)

    values = (
        user.get("username"),
        user.get("status"),
        user.get("display_name"),
        geo,
        user.get("Films"),
        user.get("This year"),
        user.get("Lists"),
        user.get("Following"),
        user.get("Followers"),
        favorites,
    )

    conn.execute(
        query,
        values,
    )


def insert_ratings(
    conn,
    ratings,
) -> None:
    """
    Insert multiple ratings using an existing
    database connection.

    Does NOT commit the transaction.
    """

    if not ratings:
        return None

    query = """
    INSERT INTO Ratings (
        user,
        liked,
        film,
        reviewed,
        rating
    )
    VALUES (?, ?, ?, ?, ?)
    """

    values = [
        (
            rating.get("user"),
            rating.get("liked"),
            rating.get("film"),
            rating.get("reviewed"),
            rating.get("rating"),
        )
        for rating in ratings
    ]

    conn.executemany(
        query,
        values,
    )


def save_user_data(
    user,
    ratings,
    db_path = DEFAULT_DB_PATH,
) -> None:
    """
    Save user and all their ratings in one transaction.

    If either operation fails, the transaction
    is rolled back automatically.
    """

    with connect(db_path) as conn:

        insert_user(
            conn=conn,
            user=user,
        )

        insert_ratings(
            conn=conn,
            ratings=ratings,
        )
