import sqlite3
import os


RATINGS_SAVE_TYPE_JSON = False #True => JSON, False => SQLITE
USERS_SAVE_TYPE_JSON = True #True => JSON, False => SQLITE

USERS_LISTED_PATH = "filmatch/data/users_listed.txt"
USERS_SCHEDULE_PATH = "filmatch/data/users_schedule.txt"
USERS_PARSED_PATH = "filmatch/data/users_parsed.txt"
RATINGS_JSON_PATH = "filmatch/data/data_ratings.json"
USERS_JSON_PATH = "filmatch/data/data_users.json"
DB_PATH = "filmatch/data/parsed_data.db"

MAX_ITERS = 10_000

def insert_ratings(
    ratings: list[dict],
    db_path: Path | str,
) -> None:

    if not ratings:
        return

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
            rating["user"],
            rating["liked"],
            rating["film"],
            rating["reviewed"],
            rating["rating"],
        )
        for rating in ratings
    ]

    with sqlite3.connect(db_path) as conn:
        conn.executemany(query, values)

def insert_user(
    user: dict,
    db_path: Path | str,
) -> None:

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

    with sqlite3.connect(db_path) as conn:
        conn.execute(query, values)

db_exists = os.path.exists(DB_PATH)

def initialize_db(db_path):
    if not db_exists:
        db = sqlite3.connect(db_path)
        c = db.cursor()
        create_tables_sql_query = """
    CREATE TABLE Ratings(
        user TEXT,
        liked INTEGER,
        film TEXT,
        reviewed INTEGER,
        rating INTEGER
    );
    CREATE TABLE Users(
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

        c.executescript(create_tables_sql_query)
        db.commit()
        db.close()
        print("tables has created")

def save_user_data(
    user,
    ratings,
    db_path,
):
    with sqlite3.connect(db_path) as conn:

        insert_user(
            conn=conn,
            user=user,
        )

        insert_ratings(
            conn=conn,
            ratings=ratings,
        )
