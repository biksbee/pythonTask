import requests
import bs4
import json
import re
from geopy.geocoders import Nominatim
from ratelimiter import RateLimiter

BASE_URL = 'https://www.ergonfoods.com'
START_PAGE = '/ergonstores'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0'
}

limiter = RateLimiter(1, 3)

geolocator = Nominatim(user_agent='biksbee')
bad_id = 'block-6336ba78aae2f009b5cf7569'
dash_rep = '\u2013'
phone_regexp = re.compile(r'(\+ ?[0-9][0-9 ]+)')


def get_phones(data: str):
    phones = phone_regexp.findall(data)
    return [phone.strip() for phone in phones]


def get_data(html: str):
    dom = bs4.BeautifulSoup(html, 'lxml')

    data = dom.find(class_='sqs-block html-block sqs-block-html')
    all_tegs = list(data.children)
    if all_tegs[0].find('h4'):
        name = all_tegs[0].find('h4').text.split(' ', 2)[2].split(', ')[0]
        data = dom.find_all(class_='sqs-block-content')[1]
        children = list(data.children)
        address = children[2]
    else:
        name = dom.find_all(class_='sqs-block-content')[0].text.split('\n', 2)[1].replace(dash_rep, ' - ')
        data = dom.find_all(class_='sqs-block-content')[2]
        children = list(data.children)
        address = children[2]

    if name == 'Balboa':
        phones = children[5].find_all('a')[1].text
    else:
        phones = get_phones(children[4].text)

    typeNow = ' '
    if name == 'Ergon Agora East Thessaloniki' or name == 'ERGON Agora':
        typeNow = 1
    elif name == 'Balboa':
        typeNow = 3
    elif name == 'Ergon Deli & Cuisine Athens International Airport Eleftherios Venizelos':
        typeNow = 4
    elif name == 'ERGON To Go' or name == 'ERGON Santorini Volkan On The Rocks':
        typeNow = 5
    elif name == 'ERGON Ikos Dassia' or name == 'ERGON Deli Maddox London' or name == 'ERGON Westfield Stratford City':
        typeNow = 6
    else:
        typeNow = 2

    type = [1, 2, 3, 4, 5, 6]

    if type[0] == typeNow:
        hours = [
            children[5].text + ' ' + children[6].text,
            children[7].text + ' ' + children[8].text,
            children[9].text + ' ' + children[10].text
        ]
    elif type[1] == typeNow:
        hours = [
            children[5].text + ' ' + children[6].text,
            children[9].text + ' ' + children[10].text
        ]
    elif type[2] == typeNow:
        hours = []
    elif type[3] == typeNow:
        hours = [
            children[5].text + ' ' + children[6].text
        ]
    elif type[4] == typeNow:
        hours = [children[3].text]
    elif type[5] == typeNow:
        hours = [
            children[5].text + ' ' + children[6].text,
            children[7].text + ' ' + children[8].text
        ]
    # noinspection PyBroadException
    try:
        location = geolocator.geocode(address.text)
    except:
        location = None

    current_time = []
    for i in hours:
        current_time.append(i.replace(dash_rep, ' - '))
    return {
        'address': address.text,
        'latlon': [location.latitude, location.longitude] if location is not None else [],
        'name': name,
        'phones': phones,
        'working_hours': current_time
    }


def process_href(href: str):
    with limiter:
        resp = requests.get(BASE_URL + href)

        resp.raise_for_status()
        return get_data(resp.text)


def main():
    html = requests.get(BASE_URL + START_PAGE, headers=headers).text
    dom = bs4.BeautifulSoup(html, 'lxml')

    links = dom.find_all(class_='list-item-content__button sqs-block-button-element sqs-block-button-element--medium sqs-button-element--primary')

    hrefs = []
    for link in links:
        if link.get('href') != '/':
            hrefs.append(link.get('href'))

    result = []
    for href in hrefs:
        result.append(process_href(href))

    print(json.dumps(result, indent=4))


if __name__ == '__main__':
    main()

