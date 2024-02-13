import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def scroll_to_bottom(driver, max_clicks=5):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

def scrape_events(driver, source):
    driver.get(source['url'])
    driver.implicitly_wait(10)

    all_events = []
    max_scroll = 5

    unique_event_urls = set()

    for _ in range(max_scroll):
        page_content = driver.page_source
        webpage = BeautifulSoup(page_content, 'html.parser')
        events = webpage.find_all(source['selectors']['event']['tag'], class_=source['selectors']['event'].get('class'))

        print(f"Found {len(events)} events on the page.")  # Adicionar esta linha para verificar quantos eventos foram encontrados

        for event in events:
            event_link = event.find('a', href=True)
            if not event_link:
                print("Event link not found.")
                continue

            event_url = 'https://www.facebook.com' + event_link['href'] if event_link['href'].startswith('/') else event_link['href']
            if event_url in unique_event_urls:
                print("Event already scraped.")
                continue

            driver.get(event_url)
            time.sleep(1)

            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            title_element = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6')
            if not title_element:
                print("Title element not found.")
                continue

            title = title_element.text.strip()

            print(f"Scraping event: {title}")  # Adicionar esta linha para verificar qual evento está sendo processado

            # Restante do código de scraping...

            location_element = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6', style="-webkit-box-orient: vertical; -webkit-line-clamp: 4; display: -webkit-box;")
            location = location_element.text.strip() if location_element else None

            organizer_element = event_page.find('span', class_='xt0psk2')
            organizer = organizer_element.text.strip() if organizer_element else None

            event_info = {
                'Title': title,
                'Description': event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip() if event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs') else None,
                'Date': event_page.find('div', class_='x1e56ztr x1xmf6yo').text.strip() if event_page.find('div', class_='x1e56ztr x1xmf6yo') else None,
                'Location': location,
                'Address': event_page.find('div', class_='xu06os2 x1ok221b').text.strip() if event_page.find('div', class_='xu06os2 x1ok221b') else None,
                'Organizer': organizer,
                'Organizer_IMG': event_page.find('img', class_='xz74otr')['src'] if event_page.find('img', class_='xz74otr') else None
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
                'Image URL': {'tag': 'img', 'class': 'event-card-image'},
                'Tags': {'tag': 'ul', 'class': 'your-ul-class-here'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
                'Image URL Organizer': {'tag': 'svg', 'class': 'eds-avatar__background eds-avatar__background--has-border'},
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
        events = scrape_events(driver, source)
        all_events.extend(events)

    print(json.dumps(all_events, indent=4))

    driver.quit()

if __name__ == "__main__":
    main()
