#%%
import httpx
from fake_useragent import UserAgent
import requests
from selectolax.parser import HTMLParser
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
ua = UserAgent()
headers = {'User-Agent':str(ua.random)}

#headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

#%%
##create database
mercado_db_colombia = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True,
    auth_plugin = 'mysql_native_password'
)

mycursor = mercado_db_colombia.cursor()

# Credentials to database connection
hostname="localhost"
dbname="mercado_db_colombia"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor.execute("DROP DATABASE  IF EXISTS mercado_db_colombia")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS mercado_db_colombia")
mycursor.execute("use mercado_db_colombia")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

#%%
link = "https://listado.mercadolibre.com.co/tv#D[A:TV]"
is_scraped = 0
def get_links(link):
    resp = requests.get(link).text
    resp = HTMLParser(resp)
    products = resp.css("li[class = 'ui-search-layout__item shops__layout-item']")
    for product in products:
        tv_link = product.css_first("a[class = 'ui-search-item__group__element shops__items-group-details ui-search-link']").attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
    next_page = resp.css_first("a[title = 'Siguiente']").attrs["href"]
    print(next_page)
    return next_page
# %%
while True:
    try:
        link = get_links(link)
    except:
        break
# %%
