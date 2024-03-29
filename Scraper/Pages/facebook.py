import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def scroll_to_bottom(driver, max_clicks=1):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

def extract_location(driver, selectors):
    page_content = driver.page_source
    webpage = BeautifulSoup(page_content, 'html.parser')
    location_element = webpage.find(selectors['Location']['tag'], class_=selectors['Location']['class'])
    if location_element:
        return location_element.text.strip()
    return None

def scrape_facebook_events(driver, url, selectors, max_scroll=5):
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

            location = extract_location(driver, selectors)

            event_info = {
                'Title': event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip(),
                'Description': event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip(),
                'Date': event_page.find('div', class_='x1e56ztr x1xmf6yo').text.strip(),
                'Location': location,
                'Address': event_page.find('div', class_='xu06os2 x1ok221b').text.strip(),
                'Organizer': event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None,
                'Organizer_IMG': event_page.find('img', class_='xz74otr')['src'] if event_page.find('img', class_='xz74otr') else None
            }

            all_events.append(event_info)
            unique_event_urls.add(event_url)

            driver.back()

            scroll_to_bottom(driver)

    return all_events

def main():
    source = {
        'name': 'Facebook',
        'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
        'selectors': {
            'event': {'tag': 'div', 'class': 'x78zum5 x1n2onr6 xh8yej3'},
            'Location': {'tag': 'span', 'class': 'nc684nl6'}
        }
    }

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    print(f"Scraping events from: {source['name']}")
    events = scrape_facebook_events(driver, source['url'], source['selectors'])

    print(json.dumps(events, indent=4))

    driver.quit()

if __name__ == "__main__":
    main()
