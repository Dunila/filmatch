from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChrmoeDriverManager
from src.scraping.discovery import discover_users
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PROJECT_ROOT / "data" / "scraping_state"

SCHEDULE_PATH = STATE_DIR / "users_schedule.txt"
LISTED_PATH = STATE_DIR / "users_listed.txt"

MAX_USERS = 1000
SAVE_EVERY = 10

def load_users(path):
    if not path.exists():
        return set()

    with path.open("r", encoding="utf-8") as file:
        return {
            line.strip() for line in file if line.strip()
        }

def save_users(path, users):
    path.parent.mkdir(
        parents=True,
        exis_ok=True
    )

    with path.open("w", encoding="utf-8") as file:
        file.write("\n".join(sorted(users)))

def save_state(
        users_schedule,
        users_listed
):
    save_users(SCHEDULE_PATH, users_schedule)

    save_users(LISTED_PATH, users_listed)

    print(f"Checkpoint saved. \n Queue: {len(users_schedule)} \n Explored {len(users_listed)}")

def create_driver():
    options = webdriver.ChromeOptions()

    #options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(
        ChrmoeDriverManager().install()
    )

    return webdriver.Chrome(
        service=service,
        options=options
    )

def main():
    users_schedule = load_users(SCHEDULE_PATH)
    users_listed = load_users(LISTED_PATH)

    print(f"Loaded {len(users_schedule)} scheduled users and {len(users_listed)} explored users")

    if not users_schedule:
        print(f"Users schedule is empty. Add at least one username to {SCHEDULE_PATH}")
        return None

    driver = create_driver()

    try:
        discover_users(
            driver=driver,
            users_schedule=users_schedule,
            users_listed=users_listed,
            max_users=MAX_USERS,
            save_every=SAVE_EVERY,
            on_checkpoint=save_state 
        )
    except KeyboardInterrupt:
        print("\n INTERRUPTED")

        save_state(
            users_schedule, users_listed
        )
    finally:
        driver.quit()

if __name__ == "__main__":
    main()