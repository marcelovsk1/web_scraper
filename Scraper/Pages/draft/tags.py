import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Defina a URL da página da web que você deseja raspar
url = "https://www.eventbrite.com/e/2024-onf-live-in-canada-montreal-tickets-775992302867?aff=ebdssbdestsearch&keep_tld=1"

# Configurações do Selenium para controlar o navegador
options = Options()
options.headless = True  # Executar o navegador em segundo plano, sem interface gráfica
driver = webdriver.Chrome(options=options)

# Carregar a página da web usando o Selenium
driver.get(url)

# Obter o código-fonte HTML da página carregada
html_content = driver.page_source

# Fechar o navegador após obter o conteúdo HTML
driver.quit()

# Criar um objeto BeautifulSoup para analisar o HTML
soup = BeautifulSoup(html_content, "html.parser")

tags_elements = soup.find_all('li', class_='tags-item inline')
tags = []
for tag_element in tags_elements:
    tag_link = tag_element.find('a')
    if tag_link:
        tags.append(tag_link.text.strip())

print(tags)
