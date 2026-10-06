from selenium.webdriver.remote.webdriver import WebDriver

from src.scraping.users import parse_user_main, parse_user_ratings
from src.data.db import insert_ratings, insert_user, save_user_data

def scrape_users(
    driver,
    usernames,
    db_path,
    max_users=None,
):
    parsed_users = set()

    for username in usernames:

        if (
            max_users is not None
            and len(parsed_users) >= max_users
        ):
            break

        print(f"Parsing {username}...")

        #parsing
        try:
            user = parse_user_main(
                username,
                driver,
            )

            ratings = parse_user_ratings(
                username,
                driver,
                sleep=0.25,
            )

        except Exception as exc:
            print(
                f"Parsing failed for "
                f"{username}: {exc}"
            )
            continue

        #validation
        if not user:
            print(
                f"Empty user data: {username}"
            )
            continue

        if user.get("username") != username:
            print(
                f"Invalid user data: {username}"
            )
            continue

        if not ratings:
            print(
                f"No ratings found for {username}"
            )

        # database
        try:
            save_user_data(
                user=user,
                ratings=ratings,
                db_path=db_path,
            )

        except Exception as exc:
            print(
                f"Database error for "
                f"{username}: {exc}"
            )
            continue

        # in case of success
        parsed_users.add(username)

        print(
            f"Saved {username}: "
            f"{len(ratings)} ratings"
        )

    return parsed_users