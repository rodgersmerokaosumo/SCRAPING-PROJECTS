#%%
import httpx
from fake_useragent import UserAgent
from selectolax.parser import HTMLParser
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
import requests
ua = UserAgent()
headers = {'User-Agent':str(ua.random)}

#headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
#%%
##create database
mercado_db_venezuela = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = mercado_db_venezuela.cursor()

# Credentials to database connection
hostname="localhost"
dbname="mercado_db_venezuela"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor.execute("DROP DATABASE  IF EXISTS mercado_db_venezuela")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS mercado_db_venezuela")
mycursor.execute("use mercado_db_venezuela")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

#%%
link = "https://televisores.mercadolibre.com.ve/tvs/"
is_scraped = 0
def get_links(link):
    r = requests.get(link, headers=headers).text
    resp = HTMLParser(r)
    current_page = resp.css_first("li[class = 'andes-pagination__button andes-pagination__button--current']").text().strip()
    page_count = resp.css_first("li[class = 'andes-pagination__page-count']").text().strip()
    page_count = int(re.findall(r'\b\d+\b', page_count)[0])
    print(f'page scraped: {current_page} of {page_count}')
    links = resp.css("a[class = 'ui-search-item__group__element shops__items-group-details ui-search-link']")
    for link in links:
        tv_link = link.attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        mercado_db_venezuela.commit()
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
