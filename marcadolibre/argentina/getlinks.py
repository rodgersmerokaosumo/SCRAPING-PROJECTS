#%%
import httpx
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
ua = UserAgent()
headers = {'User-Agent':str(ua.random)}

#headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

#%%
##create database
argentina_mercado_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = argentina_mercado_db.cursor()

mycursor.execute("DROP DATABASE  IF EXISTS argentina_mercado_db")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS argentina_mercado_db")
mycursor.execute("use argentina_mercado_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="argentina_mercado_db"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

# %%
is_scraped = 0
link = "https://listado.mercadolibre.com.ar/tv#D[A:Tv]"
def get_links(link):
    r = httpx.get(link, headers=headers).text
    resp = HTMLParser(r)
    try:
        current_page = resp.css_first("li[class = 'andes-pagination__button andes-pagination__button--current']").text().strip()
        page_count = resp.css_first("li[class = 'andes-pagination__page-count']").text().strip()
        page_count = int(re.findall(r'\b\d+\b', page_count)[0])
        print(f'page scraped: {current_page} of {page_count}')
    except:pass
    links = resp.css("a[class = 'ui-search-item__group__element shops__items-group-details ui-search-link']")
    for link in links:
        tv_link = link.attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        argentina_mercado_db.commit()
    next_page = resp.css_first("li[class = 'andes-pagination__button andes-pagination__button--next shops__pagination-button'] a").attrs["href"]

    return next_page

#%%
import re
while True:
    try:
        link = get_links(link)
    except:
        break


# %%

# %%
