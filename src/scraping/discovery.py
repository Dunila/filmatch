from scripts.scrape_utils import *
from scripts.scrape_users import *
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
import time


#Поиск новых пользователей
def parse_user_row(row):
    '''В строке на странице с following или follower юзера находит юзернейм и кол-во просмотренных фильмов знакомого из этой строки'''
    try:
        username = row.find("a", "avatar -a40")["href"].split("/")[1]
    except Exception as e:
        #print(f"{e} on username")
        username = None
    try:
        watched = int(row.find("a", "icon-watched").text.replace(",", ""))
    except Exception as e:
        #print(f"{e} on watched")
        watched = None
    return (username, watched)

def parse_network_page(soup):
    '''Из супа страницы с following или follower юзера собирает всех его знакомых, у которых есть просмотренные фильмы'''
    person_table = soup.find("table", "person-table")
    if person_table:
        rows = person_table.find("tbody").find_all("tr")
    else:
        return None
    users = list(map(parse_user_row, rows))
    users = list(filter(lambda x: x[0] and x[1] >= 50, users))
    users = [username for username, watched in users]
    return users

def parse_user_network(username, driver, to_parse_users=set(), parsed_users=set()):
    '''По юзернейму смотрит страницу с его связями и берёт всех пользователей там упомянутых'''
    init_following_url = f"https://letterboxd.com/{username}/following/"
    init_follower_url = f"https://letterboxd.com/{username}/followers/"
    users = set()

    #Смотрим всех на кого подписан пользователь и записываем всех в юзерс
    page = 1
    soup = get_soup(init_following_url, driver)
    #Осталось из легаси
    #users = parse_network_page(soup)
    while has_next(soup):
        page += 1
        following_url = f"https://letterboxd.com/{username}/following/page/{page}/"
        soup = get_soup(following_url, driver)
        page_users = parse_network_page(soup)
        page_users = list(filter(lambda x: not(x in to_parse_users or x in parsed_users), page_users))
        users.update(page_users)

    #Теперь смотрим всех, кто подписан на пользователя
    page = 1
    soup = get_soup(init_follower_url, driver)
    #Осталось из легаси
    #users = parse_network_page(soup)
    while has_next(soup):
        page += 1
        following_url = f"https://letterboxd.com/{username}/followers/page/{page}/"
        soup = get_soup(following_url, driver)
        page_users = parse_network_page(soup)
        page_users = list(filter(lambda x: not(x in to_parse_users or x in parsed_users), page_users))
        users.update(page_users)
    
    return users

def discover_users(
        driver,
        users_schedule: set[str],
        users_listed: set[str],
        max_users: int=1000,
        save_every = 10,
        on_checkpoint = None
):
    '''
    Прохождение по сети юзеров с записью в документы.

    Parameters:      
    '''
    processed = 0

    while users_schedule and processed < max_users:
        username = users_schedule.pop()

        if username in users_listed:
            continue

        print(f"[{processed + 1}/{max_users}] Exploring {username}")

        try:
            discovered_users = parse_user_network(
                username=username,
                driver=driver,
                to_parse_users=users_schedule,
                parsed_users=users_listed
            )
        except Exception as exc:
            print(f"Failed to explore {username}: {exc}")
            # continue

        users_listed.add(username)

        new_users = discovered_users.difference(users_listed)
        new_users.difference_update(users_schedule)
        users_schedule.update(new_users)

        processed += 1

        print(
            f"Found {len(new_users)} new users. \n Queue: {len(users_schedule)} \n Explored: {len(users_listed)}" 
        )

        if (on_checkpoint is not None and processed % save_every == 0):
            on_checkpoint(users_schedule, users_listed)

    if on_checkpoint is not None:
        on_checkpoint(users_schedule, users_listed)

    return users_schedule, users_listed

