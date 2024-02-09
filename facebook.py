import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Função para rolar até o final da página
def scroll_to_bottom(driver, max_scroll=3):
    for _ in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

# Função para clicar em um link de evento de forma mais robusta
def click_event_link(driver, event):
    event_link = event.find('a', href=True)
    if event_link:
        event_link.click()
        return True
    else:
        return False

# Função para raspar os eventos do Facebook
def scrape_facebook_events(driver, url, selectors):
    driver.get(url)
    driver.implicitly_wait(10)  # Defina um tempo de espera implícito menor para evitar atrasos excessivos

    all_events = []

    scroll_to_bottom(driver)  # Rolagem inicial para carregar mais eventos

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
        if click_event_link(driver, event):
            # Aguarde até que a página detalhada seja carregada completamente
            time.sleep(5)  # Aumente o tempo de espera para garantir que a página seja totalmente carregada

            # Raspe informações detalhadas da página do evento
            event_page_content = driver.page_source
            event_page = BeautifulSoup(event_page_content, 'html.parser')

            # Extrair informações detalhadas
            title = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6').text.strip() if event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6') else None
            description = event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs').text.strip() if event_page.find('div', class_='xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs') else None
            date = event_page.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1f6kntn xvq8zen x1xlr1w8 x1a1m0xk x1yc453h').text.strip() if event_page.find('span', class_='x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1f6kntn xvq8zen x1xlr1w8 x1a1m0xk x1yc453h') else None
            location = event_page.find('span', class_='xt0psk2').text.strip() if event_page.find('span', class_='xt0psk2') else None
            organizer = event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft') if event_page.find('span', class_='x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft') else None


            event_info['Title'] = title
            event_info['Description'] = description
            event_info['Date'] = date
            event_info['Location'] = location
            event_info['Organizer'] = organizer

            all_events.append(event_info)

            # Navegar de volta para a página inicial de eventos para continuar a raspagem
            driver.back()  # Voltar para a lista de eventos
        else:
            print("Link do evento não encontrado. Pulando para o próximo evento.")

    return all_events

def main():
    sources = [
        {
            'name': 'Facebook',
            'url': 'https://www.facebook.com/events/explore/montreal-quebec/102184499823699/',
            'selectors': {
                'event': {'tag': 'div', 'class': 'du4w35lb k4urcfbm l9j0dhe7 sjgh65i0'},
                'Title': {'tag': 'span', 'class': 'x1lliihq x6ikm8r x10wlt62 x1n2onr6'},
                'Description': {'tag': 'div', 'class': 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs'},
                'Date': {'tag': 'span', 'class': 'x193iq5w xeuugli x13faqbe x1vvkbs xlh3980 xvmahel x1n0sxbx x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x3x7a5m x1f6kntn xvq8zen x1xlr1w8 x1a1m0xk x1yc453h'},
                'Location': {'tag': 'span', 'class': 'xt0psk2'},
                'Image URL': {'tag': 'img', 'class': 'xz74otr x1ey2m1c x9f619 xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3'},
                'Organizer': {'tag': 'span', 'class': 'x1lliihq x6ikm8r x10wlt62 x1n2onr6 xlyipyv xuxw1ft'},
            }
        }
    ]

    all_events = []

    for source in sources:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        events = scrape_facebook_events(driver, source['url'], source['selectors'])
        driver.quit()

        source_data = {
            'source_name': source['name'],
            'events': events
        }

        all_events.append(source_data)

        # Imprimir os dados JSON no terminal
        print(json.dumps(source_data, indent=2))

    file_name = "events_data_facebook.json"  # Nome do arquivo JSON a ser criado

    with open(file_name, "w") as json_file:
        json.dump(all_events, json_file, indent=2)

    print(f"Os dados JSON foram gravados em {file_name}")

if __name__ == "__main__":
    main()
