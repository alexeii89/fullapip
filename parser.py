import json

import nums_from_string
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import PySimpleGUI as sg
import psycopg2
from time import sleep

#
def parse_links_search(search):  # parse articles in pages
    driver.get(f'https://cyberleninka.ru/search?q={search}&page=1')
    count_page = \
    nums_from_string.get_nums(driver.find_element(By.CSS_SELECTOR, "#search-box-full > h1 > span").text[20:24])[0]
    for page in range(1, count_page):
        driver.get(f'https://cyberleninka.ru/search?q={search}&page={page}')
        sleep(1)
        articles = driver.find_elements(By.CSS_SELECTOR, '#search-results > li')
        for article in articles:
            link_comm = f"""insert into public.links (link) values('{article.find_element(By.TAG_NAME, 'a').get_attribute('href')}');"""
            sqltest(link_comm)

#Serch link in db and parse
def parse_link_db():
    con = psycopg2.connect(
        database="cyberlininka",
        user="postgres",
        password="7591362+q",
        host="127.0.0.1",
        port="5432"
    )
    cur = con.cursor()
    cur.execute("select link from links where status_parsed = false;")
    parse_link = cur.fetchall()
    for link in parse_link:
        parse_page(link[0])
    driver.quit()


def parse_page(link):
    driver.get(link)
    sleep(1)
    article = {'article_name': driver.find_element(By.CSS_SELECTOR,
                                                   '#body > div.content > div > span > div:nth-child(2) > h1').text,
               'article_themes': [theme.text for theme in driver.find_elements(By.CSS_SELECTOR,
                                                                               '#body > div.content > div > span > div:nth-child(2) > div:nth-child(6) > div.half-right > ul > li')],
               'article_source_year': driver.find_element(By.CSS_SELECTOR,
                                                          '#body > div.content > div > span > div:nth-child(2) > div:nth-child(6) > div.half').text.split(
                   '\n'),
               'link': link
               }
    try:
        anonse = driver.find_element(By.CSS_SELECTOR,
                                      '#body > div.content > div > span > div:nth-child(2) > div:nth-child(8) > div > p')
        article.update({'article_anonse': anonse.text})
    except:
        article.update({'article_anonse': ''})
    source_comm = f"""insert into article_sourse (sourse_name) values ('{article['article_source_year'][1]}');"""
    sqltest(source_comm)
    article_conn = f"""insert into articles (article_name, link_id, sourse_id, year_pub, anonse) values ('{article["article_name"]}', (select id from links where link = '{article["link"]}'), (select id from article_sourse where sourse_name = '{article["article_source_year"][1]}'), '{article["article_source_year"][2][:4]}', '{article["article_anonse"]}');"""
    add_article_test(article_conn, article["link"])
    for theme in article['article_themes']:
        theme_com = f"""insert into themes (theme_name) values ('{theme}');"""
        sqltest(theme_com)
        article_theme_comm = f"""insert into article_themes (articles_id, theme_id) values ((select id from articles where article_name = '{article['article_name']}'), (select id from themes where theme_name = '{theme}'));"""
        sqltest(article_theme_comm)

# Add other in bd
def sqltest(command):
    con = psycopg2.connect(
        database="cyberlininka",
        user="postgres",
        password="7591362+q",
        host="127.0.0.1",
        port="5432"
    )
    try:
        cur = con.cursor()
        cur.execute(command)
        print('insert in db')
        con.commit()
        con.close()
    except:
        con.close()

#ADD article in bd
def add_article_test(command, link):
    con = psycopg2.connect(
        database="cyberlininka",
        user="postgres",
        password="7591362+q",
        host="127.0.0.1",
        port="5432"
    )
    try:
        cur = con.cursor()
        cur.execute(command)
        print('insert in db')
        update = f"""update public.links set status_parsed = True where link = '{link}';"""
        cur.execute(update)
        con.commit()
        con.close()
    except:
        con.close()

#Serch link from api
def search_api(search, limit):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Accept": "*/*",
        "Accept-Language": "ru,en;q=0.5",
        "Content-Type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0"
    }
    data = {"mode": "articles", "q": search, "size": int(limit), "from": 0}
    response = requests.post('https://cyberleninka.ru/api/search', headers=headers, data=json.dumps(data))
    res = json.loads(response.text)
    for link in res['articles']:
        link_comm = f"""insert into public.links (link) values('https://cyberleninka.ru{link["link"]}');"""
        sqltest(link_comm)


chrome_options = webdriver.ChromeOptions()
#Скрытый режим
#________________________________________________________________
# chrome_options.add_argument("headless")
#________________________________________________________________
# driver = webdriver.Chrome(chrome_options=chrome_options, executable_path='97/chromedriver.exe')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
# Create the Window
# Event Loop to process "events" and get the "values" of the inputs
rezult = ''
while True:
    layout = [[sg.Text('Поиск'), sg.InputText(do_not_clear=True, key='search_line', default_text=rezult)],
              [sg.Text('Поиск'), sg.InputText(do_not_clear=True, key='limit', default_text=1000)],
              [sg.Button('Поиск ссылок браузер', key='search'),
               sg.Button('Поиск ссылок API', key='search_api'),
               sg.Button('Парсинг по найденным страницам', key='parser_start'), sg.Button('Cancel')]]
    window = sg.Window('Window Title', layout)
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        driver.quit()
        break
    if event == 'search':
        rezult = values["search_line"]
        parse_links_search(rezult)
    if event == 'search_api':
        rezult = values["search_line"]
        search_api(values["search_line"], values["limit"])
    if event == 'parser_start':
        parse_link_db()
    window.close()
