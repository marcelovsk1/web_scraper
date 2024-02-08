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
            event_link = event.find('a', href=True)['href']
            driver.get(event_link)

            # Aguarde até que a página detalhada seja carregada completamente
            time.sleep(3)

            # Raspe informações detalhadas da página do evento
            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            # Modifique esta parte de acordo com a estrutura específica da página do evento no Facebook
            # Exemplo: extrair informações do título, data, local e descrição
            title = event_page.find('h1', class_='event-title css-0').text.strip() if event_page.find('h1', class_='event-title css-0') else None
            description = event_page.find('p', class_='summary').text.strip() if event_page.find('p', class_='summary') else None
            date = event_page.find('span', class_='date-info__full-datetime').text.strip() if event_page.find('span', class_='date-info__full-datetime') else None
            location = event_page.find('p', class_='location-info__address-text').text.strip() if event_page.find('p', class_='location-info__address-text') else None
            tags_container = event_page.find('li', class_='tags-item inline')  # Altere para a classe correta da sua ul
            tags = [tag.text.strip() for tag in tags_container.find_all('a')] if tags_container else None
            organizer = event_page.find('a', class_='descriptive-organizer-info__name-link') if event_page.find('a', class_='descriptive-organizer-info__name-link') else None
            image_url_organizer = event_page.find('svg', class_='eds-avatar__background eds-avatar__background--has-border') if event_page.find('svg', class_='eds-avatar__background eds-avatar__background--has-border') else None

            # Adicionar as informações detalhadas ao dicionário de informações do evento
            event_info['Title'] = title
            event_info['Description'] = description
            event_info['Date'] = date
            event_info['Location'] = location
            event_info['Tags'] = tags
            event_info['Organizer'] = organizer.text.strip() if organizer else None
            event_info['Image URL Organizer'] = image_url_organizer.get('xlink:href') if image_url_organizer else None  # Alteração aqui

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
            'name': 'Facebook',
            'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'du4w35lb k4urcfbm l9j0dhe7 sjgh65i0'},
                'Title': {'tag': 'h2', 'class': 'event-title css-0'},
                'Description': {'tag': 'p', 'class': 'summary'},
                'Date': {'tag': 'span', 'class': 'date-info__full-datetime'},
                'Location': {'tag': 'p', 'class': 'location-info__address-text'},
                'Tags': {'tag': 'ul', 'class': 'your-ul-class-here'},
                'Organizer': {'tag': 'a', 'class': 'descriptive-organizer-info__name-link'},
                'Image URL Organizer': {'tag': 'svg', 'class': 'eds-avatar__background eds-avatar__background--has-border'},
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
