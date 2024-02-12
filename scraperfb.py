import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Function to scroll to the bottom of the page
def scroll_to_bottom(driver, max_clicks=3):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

# Function to scrape the events
def scrape_events(driver, url, selectors):
    driver.get(url)
    driver.implicitly_wait(30)

    all_events = []
    max_scroll = 5  # Define the maximum number of scrolls downwards

    # Set to store unique event URLs
    unique_event_urls = set()

    for _ in range(max_scroll):
        # Collect links of events on the current page
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

            # Scrape detailed information from the event page
            event_link = event.find('a', href=True)
            if event_link:
                event_url = event_link['href']
                if event_url.startswith('/'):
                    event_url = 'https://www.facebook.com' + event_url
            else:
                # If event link is not found, skip this event
                continue

            if event_url not in unique_event_urls:
                driver.get(event_url)
                time.sleep(3)

                event_page_content = driver.page_source
                event_page = BeautifulSoup(event_page_content, 'html.parser')

                title = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip() if event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6') else None
                description = event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip() if event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs') else None
                date = event_page.find('div', class_='x1e56ztr x1xmf6yo').text.strip() if event_page.find('div', class_='x1e56ztr x1xmf6yo') else None
                location = event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None
                address_element = event_page.find('div', class_='xu06os2 x1ok221b')
                address = address_element.text.strip() if address_element else None
                organizer = event_page.find('span', class_='xt0psk2') if event_page.find('a', class_='xt0psk2') else None
                organizer_IMG = event_page.find('img', class_='xz74otr')

                event_info['Title'] = title
                event_info['Description'] = description
                event_info['Date'] = date
                event_info['Location'] = location
                event_info['Address'] = address
                event_info['Organizer'] = organizer.text.strip() if organizer else None
                event_info['Organizer_IMG'] = organizer_IMG['src'] if organizer_IMG else None

                event_list.append(event_info)

                unique_event_urls.add(event_url)

                driver.back()

        all_events.extend(event_list)

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
                'Location': {'tag': 'span', 'class': 'xt0psk2'},
                'Address': {'tag': 'div', 'class': 'xu06os2 x1ok221b'},
                'Image URL': {'tag': 'img', 'class': 'x1rg5ohu'},
            }
        }
    ]

    # Selenium settings to run the browser in the background
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in the background
    chrome_options.add_argument("--disable-gpu")  # Disable hardware acceleration

    # Selenium init
    driver = webdriver.Chrome(options=chrome_options)

    all_events = []
    for source in sources:
        print(f"Scraping events from: {source['name']}")
        events = scrape_events(driver, source['url'], source['selectors'])
        all_events.extend(events)

    # JSON
    print(json.dumps(all_events, indent=4))

    driver.quit()

if __name__ == "__main__":
    main()
