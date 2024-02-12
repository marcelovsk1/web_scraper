import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Função para rolar até o final da página
def scroll_to_bottom(driver, max_clicks=3):
    for _ in range(max_clicks):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

# Função para raspar os eventos
def scrape_events(driver, url, selectors, max_pages=1):
    driver.get(url)
    driver.implicitly_wait(30)

    all_events = []

    for _ in range(max_pages):
        # Coletar links dos eventos na página atual
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

            # Clique no link do evento para acessar a página detalhada
            event_link = event.find('a', href=True)
            if event_link:
                event_url = event_link['href']
                if event_url.startswith('/'):
                    event_url = 'https://www.facebook.com' + event_url

                driver.get(event_url)

                time.sleep(3)

                # Raspe informações detalhadas da página do evento
                event_page_content = driver.page_source
                event_page = BeautifulSoup(event_page_content, 'html.parser')

                title = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip() if event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6') else None
                description = event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip() if event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs') else None
                date = event_page.find('div', class_='x1e56ztr x1xmf6yo').text.strip() if event_page.find('div', class_='x1e56ztr x1xmf6yo') else None
                location = event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None
                organizer = event_page.find('span', class_='xt0psk2') if event_page.find('a', class_='xt0psk2') else None

                event_info['Title'] = title
                event_info['Description'] = description
                event_info['Date'] = date
                event_info['Location'] = location
                event_info['Organizer'] = organizer.text.strip() if organizer else None

                event_list.append(event_info)

                driver.back()

        all_events.extend(event_list)

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
            'name': 'Facebook',
            'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'x6s0dn4 x78zum5 x1a02dak xw7yly9 xcud41i xat24cr x139jcc6'},
                'Title': {'tag': 'span', 'class': 'x1lliihq x6ikm8r x10wlt62 x1n2onr6'},
                'Description': {'tag': 'div', 'class': 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs'},
                'Date': {'tag': 'div', 'class': 'x1e56ztr x1xmf6yo'},
                'Location': {'tag': 'span', 'class': 'xt0psk2'},
                'Image URL': {'tag': 'div', 'class': 'x1qjc9v5 x1q0q8m5 x1qhh985 xu3j5b3 xcfux6l x26u7qi xm0m39n x13fuv20 x972fbf x1ey2m1c x9f619 x78zum5 xds687c xdt5ytf x1iyjqo2 xs83m0k x1qughib xat24cr x11i5rnm x1mh8g0r xdj266r x2lwn1j xeuugli x18d9i69 x4uap5 xkhd6sd xexx8yu x10l6tqk x17qophe x13vifvy x1ja2u2z'},
            }
        }
    ]

    # Configurações do Selenium para executar o navegador em segundo plano
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Execute o Chrome em segundo plano
    chrome_options.add_argument("--disable-gpu")  # Desative a aceleração de hardware

    # Inicializar o driver do Selenium
    driver = webdriver.Chrome(options=chrome_options)

    # Raspagem de eventos de todas as fontes especificadas
    all_events = []
    for source in sources:
        print(f"Raspar eventos da fonte: {source['name']}")
        events = scrape_events(driver, source['url'], source['selectors'])
        all_events.extend(events)

    # Salvar os eventos em formato JSON no terminal
    print(json.dumps(all_events, indent=4))

    # Fechar o driver do Selenium após a conclusão da raspagem
    driver.quit()

if __name__ == "__main__":
    main()
