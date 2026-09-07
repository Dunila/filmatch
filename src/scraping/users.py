from scripts.scrape_utils import *
from scripts.scrape_users import *
from bs4 import BeautifulSoup
import time


#Парсинг оценок пользователя со страниц пользователь-фильм
def find_poster_link(poster):
    '''Ищет на элементе постера на стр.пользователя-фильмы ссылку на этот фильм'''
    element = poster.find("div")
    link = element.get("data-target-link")
    if not link:
        link = element.get("data-film-link")
    return link.split("/")[-2]

def find_poster_rating(poster):
    '''С элемента с постером на стр.пользователя-фильмы ищет рейтинг пользователя на этот фильм'''
    return int(poster.find("p", "poster-viewingdata").find("span")["class"][-1].split("-")[-1])

def find_poster_liked(poster):
    '''С элемента с постером на стр.пользователя-фильмы  ищет лайкнул ли пользователь этот фильм'''
    try:
        if poster.find("p", "poster-viewingdata").find("span", "like"):
            liked = 1
        else:
            liked = 0
    except Exception as e:
        liked = 0
    return liked

def find_poster_reviewed(poster):
    '''С элемента с постером на стр.пользователя-фильмы  ищет комментил ли пользователь этот фильм'''
    try:
        if poster.find("p", "poster-viewingdata").find("a", "review-micro has-icon icon-review tooltip"):
            reviewed = 1
        else:
            reviewed = 0
    except Exception as e:
        reviewed = 0
    return reviewed

def handle_poster(poster, user):
    '''Собирает инфу о взаимодействии юзера и фильма с постера со стр. пользователь-фильмы и пакует в словарик'''
    liked = find_poster_liked(poster)
    link = find_poster_link(poster)
    reviewed = find_poster_reviewed(poster)
    rating = find_poster_rating(poster)
    return {
        "user": user,
        "liked": liked,
        "film": link,
        "reviewed": reviewed,
        "rating": rating
    }

def parse_ratings_page(soup, user):
    '''Берёт суп с одной страницей пользователь-фильмы и собирает инфу о взаимодействии юзера и фильма в список словарей'''
    try:
        films = soup.find("body").find("ul", "grid -p70").find_all("li") #poster-list -p70 -grid film-list clear
        # test1 = soup.find("body")
        # print(f"test1: {test1}")
        # test1 = test1.find("ul", "poster-list -p70 -grid film-list clear")
        # print(f"test3: {test1}")
        # test1 = test1.find_all("li")
        # print(f"test3: {test1}")

        user_ratings = list(map(lambda x: handle_poster(x, user), films))
        time.sleep(5)
        return user_ratings
    except Exception as e:
        print(f"Failed parge rating page. Error: {e}")
        time.sleep(5)
        return []

def parse_user_ratings(username, driver, sleep=None):
    '''По юзернейму парсит все его оценки со страниц пользователь-фильм'''
    init_page = f"https://letterboxd.com/{username}/films/rated/.5-5/"
    soup = get_soup(init_page, driver=driver)
    pages_cnt = get_pages_cnt(soup)
    
    user_ratings = []
    user_ratings.extend(parse_ratings_page(soup, username))
    if pages_cnt > 1:
        for page in range(2, pages_cnt+1):
            if sleep:
                time.sleep(sleep)
            page_url = f"https://letterboxd.com/{username}/films/rated/.5-5/page/{page}/"
            soup = get_soup(page_url, driver=driver)
            user_ratings.extend(parse_ratings_page(soup, username))
    return user_ratings

#Парсинг доп инфы о юзере
def find_display_name(soup):
    '''Ищет в супе страницы юзера его отображаемое имя'''
    try:
        display_name = soup.find("span", "displayname tooltip").text
    except Exception as e:
        display_name = None
    return {"display_name": display_name}

def find_status(soup):
    '''Находит статус пользователя member/pro итд'''
    try:
        status = soup.find("span", "badge").text
    except Exception as e:
        status = "member"
    return {"status": status}

def find_tags_on_svg(soup, tag_name, tag_svg):
    '''Находит свг в описании профиля, мб гео, но бесполезно по опыту'''
    try:
        tag = soup.find("div", "profile-metadata js-profile-metadata").find("path", d=tag_svg).find_next("span").text
    except Exception as e:
        print(f"exception {e}")
        tag = None
    if tag and tag_name == "geo":
        tag = [tag] if ',' not in tag else tag.split(', ')
    return {tag_name: tag}

def get_exact_stat(stat):
    '''Обрабатывает статистику с '''
    try:
        whole_text, value = stat.text, stat.find("span").text
    except:
        return {}
    key = whole_text[len(value):]
    value = int(value.replace(",", ""))
    return (key, value)

def get_stats(soup):
    '''Ищет заголовки со статой юзера в специальной строке на странице'''
    stats_list = soup.find_all("h4", "profile-statistic")
    stats_list = list(map(get_exact_stat, stats_list))
    stats = {key: value for key, value in stats_list}
    stats.setdefault("Films", None)
    stats.setdefault("This year", None)
    stats.setdefault("Lists", None)
    stats.setdefault("Following", None)
    stats.setdefault("Followers", None)
    return stats

def find_favorities(soup):
    '''Находит элемент с любимыми фильмами юзера'''
    try:
        favs = soup.find_all("li", "favourite-film-poster-container")
        favs = list(map(lambda x: x.find("div")["data-film-slug"], favs))
    except Exception as e:
        favs = []
    return {"favorities": favs}

geo_svg = "M4.25 2.735a.749.749 0 111.5 0 .749.749 0 11-1.5 0zM8 4.75c0-2.21-1.79-4-4-4s-4 1.79-4 4a4 4 0 003.5 3.97v6.53h1V8.72A4 4 0 008 4.75z"

def get_general_user_info(soup):
    '''Собирает всю информацию о юзере в один словарь'''
    result = {}
    result.update(find_display_name(soup))
    result.update(find_status(soup))
    result.update(find_tags_on_svg(soup, "geo", tag_svg=geo_svg))
    result.update(get_stats(soup))
    result.update(find_favorities(soup))
    return result

def parse_user_main(username, driver):
    '''По имени юзера возвращает о нём инфу с главной стр.'''
    main_page_url = f"https://letterboxd.com/{username}/"
    soup = get_soup(main_page_url, driver)
    user = {}
    user = get_general_user_info(soup)
    user.update({"username": username})
    return user
