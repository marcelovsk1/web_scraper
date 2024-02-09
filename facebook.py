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

# Função para raspar os eventos do Facebook
def scrape_facebook_events(driver, url, selectors, max_pages=1):
    driver.get(url)
    driver.implicitly_wait(30)

    all_events = []

    for _ in range(max_pages):
        # Coletar links dos eventos na página atual
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

            # Clique no link do evento para acessar a página detalhada
            event_link = event.find('a', href=True)['href']
            driver.get(event_link)

            # Aguarde até que a página detalhada seja carregada completamente
            time.sleep(3)

            # Raspe informações detalhadas da página do evento
            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            # Extrair informações detalhadas
            title = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip() if event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6') else None
            description = event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip() if event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs') else None
            date = event_page.find('span', class_='date-info__full-datetime').text.strip() if event_page.find('span', class_='date-info__full-datetime') else None
            location = event_page.find('p', class_='location-info__address-text').text.strip() if event_page.find('p', class_='location-info__address-text') else None
            organizer = event_page.find('a', class_='descriptive-organizer-info__name-link') if event_page.find('a', class_='descriptive-organizer-info__name-link') else None

            event_info['Title'] = title
            event_info['Description'] = description
            event_info['Date'] = date
            event_info['Location'] = location
            event_info['Organizer'] = organizer

            # Adicionar o evento à lista de eventos
            all_events.append(event_info)

            # Navegar de volta para a página inicial de eventos para continuar a raspagem
            driver.back()  # Voltar para a lista de eventos

        # Avançar para a próxima página de eventos
        try:
            next_button = driver.find_element_by_xpath("//a[contains(text(), 'Next')]")
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
                'event': {'tag': 'div', 'class': 'du4w35lb k4urcfbm l9j0dhe7 sjgh65i0'},
                'Title': {'tag': 'h2', 'class': 'Typography_root__487rx #3a3247 Typography_body-lg__487rx event-card__clamp-line--two Typography_align-match-parent__487rx'},
                'Description': {'tag': 'p', 'class': 'summary'},
                'Date': {'tag': 'p', 'class': 'Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx'},
                'Location': {'tag': 'p', 'class': 'Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx'},
                'Image URL': {'tag': 'img', 'class': 'event-card-image'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
            }
        }
    ]

    all_events = []

    for source in sources:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        events = scrape_facebook_events(driver, source['url'], source['selectors'], max_pages=5)
        driver.quit()

        source_data = {
            'source_name': source['name'],
            'events': events
        }

        all_events.append(source_data)

    file_name = "events_data_facebook.json"  # Nome do arquivo JSON a ser criado

    with open(file_name, "w") as json_file:
        json.dump(all_events, json_file, indent=2)

    print(f"Os dados JSON foram gravados em {file_name}")

    # Carregar o arquivo JSON
    with open(file_name, 'r') as file:
        data = json.load(file)

    # Imprimir o conteúdo do arquivo JSON no terminal
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
