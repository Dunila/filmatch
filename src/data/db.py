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

def insert_rating(rating, cursor):
    sql_query = '''
    INSERT INTO Ratings(user, liked, film, reviewed, rating)
    VALUES (?, ?, ?, ?, ?)
    '''
    cursor.execute(sql_query, (
        rating.get("user"),
        rating.get("liked"),
        rating.get("film"),
        rating.get("reviewed"),
        rating.get("rating")
    ))

def insert_user(user, cursor):
    sql_query = f'''
    INSERT INTO Users(username, status, display_name, geo, films, thisyear, lists, following, followers, favorities)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    geo = user.get("geo")
    if geo:
        if len(geo) == 1:
            geo = geo[0]
        else:
            geo = ", ".join(geo)
    favorities = user.get("favorities")
    if favorities:
        if len(favorities) == 1:
            favorities = favorities[0]
        else:
            favorities = ", ".join(favorities)
    cursor.execute(sql_query, (
        user.get("username"),
        user.get("status"),
        user.get("display_name"),
        geo,
        user.get("Films"),
        user.get("This year"),
        user.get("Lists"),
        user.get("Following"),
        user.get("Followers"),
        favorities
    ))

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