import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def scroll_to_bottom(driver, max_clicks=1):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

def scrape_events(driver, url, selectors, max_pages=1):
    driver.get(url)
    driver.implicitly_wait(30)

    all_events = []

    for _ in range(max_pages):

        page_content = driver.page_source
        webpage = BeautifulSoup(page_content, 'html.parser')
        events = webpage.find_all(selectors['event']['tag'], class_=selectors['event'].get('class'))

        event_list = []

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

            # Adicionar as informações detalhadas ao dicionário de informações do evento
            event_info['Title'] = title
            event_info['Description'] = description
            event_info['Price'] = price
            event_info['Date'] = date
            event_info['Location'] = location
            event_info['Tags'] = tags
            event_info['Organizer'] = organizer.text.strip() if organizer else None

            # Adicionar o evento à lista de eventos
            event_list.append(event_info)

            # Navegar de volta para a página inicial de eventos para continuar a raspagem
            driver.get(url)

        all_events.extend(event_list)

        # Avançar para a próxima página de eventos
        try:
            next_button = driver.find_element_by_link_text('Next')
            next_button.click()
            time.sleep(3)
        except:
            break  # Se não houver mais botão "Next", saia do loop

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
                'Image URL': {'tag': 'img', 'class': 'event-card-image'},
                'Tags': {'tag': 'ul', 'class': 'your-ul-class-here'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
                'Image URL Organizer': {'tag': 'svg', 'class': 'eds-avatar__background eds-avatar__background--has-border'},
            },
        }
    ]

    all_events = []

    for source in sources:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        events = scrape_events(driver, source['url'], source['selectors'], max_pages=5)
        driver.quit()

        source_data = {
            'source_name': source['name'],
            'events': events
        }

        all_events.append(source_data)

    file_name = "events_data.json"

    with open(file_name, "w") as json_file:
        json.dump(all_events, json_file, indent=2)

    print(f"Os dados JSON foram gravados em {file_name}")

    # JSON
    with open(file_name, 'r') as file:
        data = json.load(file)

    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
