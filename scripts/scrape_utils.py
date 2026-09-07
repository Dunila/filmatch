from bs4 import BeautifulSoup


def get_soup(url, driver):
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html)
    return soup

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
