import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from fuzzywuzzy import fuzz
from datetime import datetime

import soupsieve

def scroll_to_bottom(driver, max_clicks=1):
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

def get_previous_page_image_url(driver):
    # URL da página anterior
    url = 'https://www.eventbrite.com/d/canada--montreal/all-events/?page=1'

    # Fazendo a requisição HTTP
    driver.get(url)

    # Verificando se a requisição foi bem-sucedida
    if driver.page_source:
        # Parsing do HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Encontrando a tag img com a classe 'event-card-image'
        img_tag = soup.find('img', class_='event-card-image')

        # Verificando se a tag img foi encontrada
        if img_tag:
            # Obtendo a URL da imagem do atributo src
            return img_tag['src']

    return None

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
                    if key == 'ImageURL':
                        event_info[key] = element['src'] if element and 'src' in element.attrs else None

            event_link = event.find('a', href=True)['href']
            driver.get(event_link)

            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            title = event_page.find('h1', class_='event-title css-0').text.strip() if event_page.find('h1', class_='event-title css-0') else None
            description = event_page.find('p', class_='summary').text.strip() if event_page.find('p', class_='summary') else None
            price = event_page.find('div', class_='conversion-bar__panel-info').text.strip() if event_page.find('div', class_='conversion-bar__panel-info') else None
            date = event_page.find('span', class_='date-info__full-datetime').text.strip() if event_page.find('span', class_='date-info__full-datetime') else None
            location_element = event_page.find('div', class_='location-info__address')
            location = location_element.text.strip() if location_element else None
            ImageURL = get_previous_page_image_url(driver)
            tags_elements = event_page.find_all('li', class_='tags-item inline')
            tags = []
            for tag_element in tags_elements:
                tag_link = tag_element.find('a')
                if tag_link:
                    tags.append(tag_link.text.strip())
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
            event_info['ImageURL'] = ImageURL
            event_info['Tags'] = tags
            event_info['Organizer'] = organizer.text.strip() if organizer else None
            event_info['EventUrl'] = event_link  # Adiciona o EventUrl ao dicionário


            all_events.append(event_info)

            driver.back()

        try:
            # Tenta encontrar e clicar no botão "Next"
            next_button = driver.find_element_by_link_text('Next')
            next_button.click()
        except:
            # Se não encontrar o botão "Next" ou ocorrer algum erro, sai do loop
            break

    return all_events


def main():
    sources = [
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
                'ImageURL': {'tag': 'img', 'class': 'hero-img'},
                'Tags': {'tag': 'ul', 'class': 'your-ul-class-here'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
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

    print(json.dumps(all_events, indent=4))

    driver.quit()

if __name__ == "__main__":
    main()
