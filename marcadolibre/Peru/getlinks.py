#%%
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
ua = UserAgent()
headers = {'User-Agent':str(ua.random)}

#headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

#%%
##create database
mercado_db_peru = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = mercado_db_peru.cursor()

# Credentials to database connection
hostname="localhost"
dbname="mercado_db_peru"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor.execute("DROP DATABASE  IF EXISTS mercado_db_peru")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS mercado_db_peru")
mycursor.execute("use mercado_db_peru")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

#%%
link = "https://listado.mercadolibre.com.pe/tv#D[A:tv]"
is_scraped = 0

# %%
def get_links(link):
    r = requests.get(link).text
    soup = BeautifulSoup(r, 'lxml')
    products = soup.find_all("li", class_ = "ui-search-layout__item shops__layout-item")
    for product in products:
        product_link = product.find("a").get("href")
        print(product_link)
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (product_link, is_scraped))
        mercado_db_peru.commit()
# %%
while True:
    get_links(link)
    try:
        r = requests.get(link).text
        soup = BeautifulSoup(r, 'lxml')
        next = soup.find("li", class_ = "andes-pagination__button andes-pagination__button--next shops__pagination-button")
        url = next.find("a").get("href")
        link = url
    except: break

# %%
