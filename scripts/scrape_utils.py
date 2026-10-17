from bs4 import BeautifulSoup
import time


# def get_soup(url, driver):
#     driver.get(url)
#     html = driver.page_source
#     soup = BeautifulSoup(html, "html.parser")
#     return soup

def get_soup(url, driver):
    driver.get(url)

    for attempt in range(30):
        html = driver.page_source

        if (
            "Выполнение проверки безопасности" not in html
            and "Just a moment" not in driver.title
            and "cf_chl_opt" not in html
        ):
            return BeautifulSoup(html, "html.parser")

        if attempt == 0:
            print(
                "Cloudflare security check detected. "
                "Complete the check in the browser."
            )

        time.sleep(2)

    raise RuntimeError(
        f"Letterboxd security check did not finish: {url}"
    )

def get_pages_cnt(soup):
    pages_list = soup.find_all("li", "paginate-page")
    if not pages_list:
        page_cnt = [1]
    try:
        page_cnt = int(pages_list[-1].text)
    except ValueError:
        print(f"Could not be converted {pages_list[-1].text}")
        page_cnt = 1
    except Exception as e:
        #print(e)
        page_cnt = 1
    return page_cnt

def has_next(soup):
    return True if soup.find("a", "next") else False
