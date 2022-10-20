import bs4
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from geopy.geocoders import Nominatim


BASE_URL = 'https://oriencoop.cl/'
START_PAGE = 'sucursales.htm'

headers = {
    # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0"
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Cookie': 'BITRIX_SM_DETECTED=N; PHPSESSID=eDNLys66bt0qoi7AEmuKcH7WzYYnn6yy; BITRIX_SM_CITY_ID=3325; BITRIX_SM_GUEST_ID=7857995; BITRIX_SM_LAST_VISIT=20.10.2022%2015%3A53%3A06; BITRIX_SM_SALE_UID=63612005; BITRIX_CONVERSION_CONTEXT_s1=%7B%22ID%22%3A3%2C%22EXPIRE%22%3A1666292340%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D; POLICY=Y',
    'Host': 'som1.ru',
    'Pragma': 'no-cache',
    'Referer': 'https://som1.ru/shops//bitrix/js/main/',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    'TE': 'trailers',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'

}

pool = ThreadPoolExecutor(max_workers=2)
geolocator = Nominatim(user_agent='biksbee')
pattern = ', local 2A'


def get_data(html: str):
    dom = bs4.BeautifulSoup(html, 'html.parser')

    data = dom.find(class_='s-dato')
    children = list(data.children)

    name = children[1]
    address = children[3].find('span').text
    phone = children[5].find('span').text

    hours = [
        span.text.lstrip()
        for span in children[9].find_all('span')
    ]

    location = geolocator.geocode(address.replace(pattern, ''))

    return {
        'address': address,
        'latlon': [location.latitude, location.longitude],
        'name': name.text,
        'phones': phone,
        'working_hours': hours,
    }


def process_href(href: str):
    resp = requests.get(BASE_URL + href)

    resp.raise_for_status()
    return get_data(resp.text)


def main():
    html = requests.get(BASE_URL + START_PAGE, headers=headers).text
    dom = bs4.BeautifulSoup(html, 'html.parser')

    links = dom.find_all(class_='sub-menu')

    hrefs = []
    for link in links:
        for a_link in link.find_all('a'):
            hrefs.append(a_link.get('href'))

    futures = []
    for href in hrefs:
        futures.append(pool.submit(process_href, href))

    result = []
    for future in futures:
        result.append(future.result())

    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()
