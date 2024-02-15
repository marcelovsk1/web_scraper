import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from fuzzywuzzy import fuzz
from datetime import datetime

def scroll_to_bottom(driver, max_clicks=5):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

def calculate_similarity(str1, str2):
    return fuzz.token_sort_ratio(str1, str2)

from datetime import datetime

def format_date(date_str, source):
    #%A: Represents the full name of the day of the week (for example, "Sunday").
    #%B: Represents the full name of the month (for example, "March").
    #%d: Represents the day of the month as a decimal number (for example, "03").
    #%Y: Represents the four-digit year (for example, "2024").
    if source == 'Facebook':
        # Facebook: SUNDAY, MARCH 3, 2024
        formatted_date = datetime.strptime(date_str, '%A, %B %d, %Y')
        return formatted_date
    elif source == 'Eventbrite':
        # Eventbrite: Sunday, March 3
        formatted_date = datetime.strptime(date_str, '%A, %B %d')
        return formatted_date
    else:
        # Trate outras fontes, se necessário
        return None


def format_location(location_str, source):
    if source == 'Facebook':
        # Se a localização contiver uma vírgula, dividimos em nome do local e endereço
        if ',' in location_str:
            location, address = location_str.split(',', 1)
            return {
                'Location': location.strip(),
                'Address': address.strip()
            }
        else:
            # Se não houver vírgula, assumimos que é apenas o nome do local
            return {
                'Location': location_str.strip(),
                'Address': None
            }
    elif source == 'Eventbrite':
        # O Eventbrite já fornece a localização e o endereço separados
        return {
            'Location': location_str.strip(),
            'Address': None  # Não precisamos do endereço separado para o Eventbrite
        }
    else:
        # Trate outras fontes, se necessário
        return None


def scrape_facebook_events(driver, url, selectors, max_scroll=1):
    driver.get(url)
    driver.implicitly_wait(10)

    all_events = []
    unique_event_urls = set()

    for _ in range(max_scroll):
        page_content = driver.page_source
        webpage = BeautifulSoup(page_content, 'html.parser')
        events = webpage.find_all(selectors['event']['tag'], class_=selectors['event'].get('class'))

        for event in events:
            event_link = event.find('a', href=True)
            if not event_link:
                continue

            event_url = 'https://www.facebook.com' + event_link['href'] if event_link['href'].startswith('/') else event_link['href']
            if event_url in unique_event_urls:
                continue

            driver.get(event_url)
            time.sleep(1)

            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            event_info = {
                'Title': event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip(),
                'Description': event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip(),
                'Date': event_page.find('div', class_='x1e56ztr x1xmf6yo').text.strip() if event_page.find('div', class_='x1e56ztr x1xmf6yo') else None,
                'Location': event_page.find('div', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f').text.strip() if event_page.find('div', class_='x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz xt0b8zv xzsf02u x1s688f') else None,
                'ImageURL': event_page.find('img', class_='xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3')['src'] if event_page.find('img', class_='xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3') else None,
                'Organizer': event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None,
                'Organizer_IMG': event_page.find('img', class_='xz74otr')['src'] if event_page.find('img', class_='xz74otr') else None,
                'EventUrl': event_url  # Adicionando o link do evento ao dicionário
            }

            all_events.append(event_info)
            unique_event_urls.add(event_url)

            driver.back()

        scroll_to_bottom(driver)

    return all_events


def main():
    sources = [
        {
            'name': 'Facebook',
            'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'x78zum5 x1n2onr6 xh8yej3'},
                'Title': {'tag': 'span', 'class': 'x1lliihq x6ikm8r x10wlt62 x1n2onr6'},
                'Description': {'tag': 'div', 'class': 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs'},
                'Date': {'tag': 'div', 'class': 'x1e56ztr x1xmf6yo'},
                'Location': {'tag': 'span', 'class': 'x1lliihq x6ikm8r x10wlt62 x1n2onr6'},
                'ImageURL': {'tag': 'img', 'class': 'xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3'},
                'Organizer': {'tag': 'span', 'class': 'xt0psk2'},
                'Organizer_IMG': {'tag': 'img', 'class': 'xz74otr'}
            }
        }
    ]

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    all_events = []
    for source in sources:
        print(f"Scraping events from: {source['name']}")
        if source['name'] == 'Facebook':
            events = scrape_facebook_events(driver, source['url'], source['selectors'])
        elif source['name'] == 'Eventbrite':
            events = scrape_eventbrite_events(driver, source['url'], source['selectors'])
        else:
            print(f"Unsupported source: {source['name']}")
            continue
        all_events.extend(events)

    print(json.dumps(all_events, indent=4))

    driver.quit()

if __name__ == "__main__":
    main()
