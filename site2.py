import bs4
import requests
import json
from concurrent.futures import ThreadPoolExecutor
from geopy.geocoders import Nominatim


BASE_URL = 'https://som1.ru'
START_PAGE = '/shops/'

headers = {
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

geolocator = Nominatim(user_agent='biksbee')
pool = ThreadPoolExecutor(max_workers=10)


def get_data(html: str):
    dom = bs4.BeautifulSoup(html, 'lxml')
    data = dom.find(class_='shop-info-table')
    children = list(data.children)

    name = dom.find('h1')
    address = children[1].find_all('td')[2].text
    phones = children[3].find_all('td')[2].text.split(',')
    hours = children[5].find_all('td')[2].text.split(',')

    try:
        location = geolocator.geocode(address.text)
    except:
        location = None

    return {
        'address': address,
        'latlon': [location.latitude, location.longitude] if location is not None else [],
        'name': name.text,
        'phones': phones,
        'working_hours': hours
    }


def process_href(href: str):
    resp = requests.get(BASE_URL + href, headers=headers)

    resp.raise_for_status()
    return get_data(resp.text)



def main():
    html = requests.get(BASE_URL + START_PAGE, headers=headers).text
    dom = bs4.BeautifulSoup(html, 'lxml')

    id_s = []
    regions = dom.find_all(class_='city-title-desc')
    for region in regions:
        id_s.append(region.get('id'))

    city_s = []
    city_s = dom.find_all(class_='cities-container')

    current_tag = []
    for i in city_s:
        current_tag.append(i.find_all('label'))

    id_city = []
    for i in current_tag:
        for j in i:
            id_city.append(j.get('id'))  # ID EVERYONE CITY

    buttons = []
    for idc in id_city:
        myobj = {
            'CITY_ID': idc
        }
        x = (requests.post(BASE_URL + START_PAGE, headers=headers, json=myobj).text)
        buttons.append(bs4.BeautifulSoup(x, 'lxml').find(class_='btn btn-blue'))


    hrefs = []
    for button in buttons:
        hrefs.append(button.get('href'))

    result = []
    for href in hrefs:
        result.append(process_href(href))


    print(json.dumps(result, indent=4))

if __name__ == '__main__':
    main()