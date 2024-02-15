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
                'Location': event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip(),
                'ImageURL': event_page.find('img', class_='xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3')['src'] if event_page.find('img', class_='xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3') else None,
                'Address': event_page.find('div', class_='xu06os2 x1ok221b').text.strip(),
                'Organizer': event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None,
                'Organizer_IMG': event_page.find('img', class_='xz74otr')['src'] if event_page.find('img', class_='xz74otr') else None,
                'EventUrl': event_url
            }

            all_events.append(event_info)
            unique_event_urls.add(event_url)

            driver.back()

        scroll_to_bottom(driver)

    return all_events


def scrape_eventbrite_events(driver, url, selectors, max_pages=1):
    driver.get(url)
    driver.implicitly_wait(30)

    all_events = []

    for _ in range(max_pages):
        page_content = driver.page_source
        webpage = BeautifulSoup(page_content, 'html.parser')
        events = webpage.find_all(selectors['event']['tag'], class_=selectors['event'].get('class'))

        for event in events:
            event_info = {}
            for key, selector in selectors.items():
                if key != 'event':
                    element = event.find(selector['tag'], class_=selector.get('class'))
                    event_info[key] = element.text.strip() if element else None
                    if key == 'Image URL':
                        event_info[key] = element['src'] if element and 'src' in element.attrs else None

            event_link = event.find('a', href=True)['href']
            driver.get(event_link)
            time.sleep(3)

            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            title = event_page.find('h1', class_='event-title css-0').text.strip() if event_page.find('h1', class_='event-title css-0') else None
            description = event_page.find('p', class_='summary').text.strip() if event_page.find('p', class_='summary') else None
            price = event_page.find('div', class_='conversion-bar__panel-info').text.strip() if event_page.find('div', class_='conversion-bar__panel-info') else None
            date = event_page.find('span', class_='date-info__full-datetime').text.strip() if event_page.find('span', class_='date-info__full-datetime') else None
            location = event_page.find('p', class_='location-info__address-text').text.strip() if event_page.find('p', class_='location-info__address-text') else None
            address_element = event_page.find('p', class_='location-info__address-text')
            address = address_element.text.strip() if address_element else None
            tags_container = event_page.find('li', class_='tags-item inline')  # Altere para a classe correta da sua ul
            tags = [tag.text.strip() for tag in tags_container.find_all('a')] if tags_container else None
            organizer = event_page.find('a', class_='descriptive-organizer-info__name-link') if event_page.find('a', class_='descriptive-organizer-info__name-link') else None
            image_url_organizer = event_page.find('svg', class_='eds-avatar__background eds-avatar__background--has-border')
            if image_url_organizer:
                image_tag = image_url_organizer.find('image')
                if image_tag:
                    event_info['Image URL Organizer'] = image_tag.get('xlink:href')
                else:
                    event_info['Image URL Organizer'] = None
            else:
                event_info['Image URL Organizer'] = None

            event_info['Title'] = title
            event_info['Description'] = description
            event_info['Price'] = price
            event_info['Date'] = date
            event_info['Location'] = location
            event_info['Address'] = address
            event_info['Tags'] = tags
            event_info['Organizer'] = organizer.text.strip() if organizer else None
            event_info['EventUrl'] = event_link  # Adiciona o EventUrl ao dicionário

            all_events.append(event_info)

            driver.back()
            time.sleep(3)  # Adiciona um tempo de espera para evitar bloqueios

        try:
            # Tenta encontrar e clicar no botão "Next"
            next_button = driver.find_element_by_link_text('Next')
            next_button.click()
            time.sleep(3)
        except:
            # Se não encontrar o botão "Next" ou ocorrer algum erro, sai do loop
            break

    return all_events

def find_unique_events(events):
    unique_events = []
    seen_titles = set()
    for event in events:
        title = event['Title']
        if title not in seen_titles:
            unique_events.append(event)
            seen_titles.add(title)
    return unique_events

def main():
    sources = [
        {
            'name': 'Facebook',
            'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'x78zum5 x1n2onr6 xh8yej3'}
            }
        },
        {
            'name': 'Eventbrite',
            'url': 'https://www.eventbrite.com/d/canada--montreal/all-events/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'discover-search-desktop-card discover-search-desktop-card--hiddeable'},
                'Title': {'tag': 'h2', 'class': 'Typography_root__487rx #3a3247 Typography_body-lg__487rx event-card__clamp-line--two Typography_align-match-parent__487rx'},
                'Description': {'tag': 'p', 'class': 'summary'},
                'Date': {'tag': 'p', 'class': 'Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx'},
                'Location': {'tag': 'p', 'class': 'Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx'},
                'Price': {'tag': 'p', 'class': 'Typography_root__487rx #3a3247 Typography_body-md-bold__487rx Typography_align-match-parent__487rx'},
                'ImageURL': {'tag': 'img', 'class': 'event-card-image'},
                'Tags': {'tag': 'ul', 'class': 'your-ul-class-here'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
                'Organizer_IMG': {'tag': 'svg', 'class': 'eds-avatar__background eds-avatar__background--has-border'},
            },
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

    # Find unique events
    unique_events = find_unique_events(all_events)

    # Save unique events to JSON file
    with open('unique_events.json', 'w') as f:
        json.dump(unique_events, f, indent=4)

    driver.quit()

if __name__ == "__main__":
    main()
