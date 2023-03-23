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
chile_mercado_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = chile_mercado_db.cursor()

mycursor.execute("DROP DATABASE  IF EXISTS chile_mercado_db")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS chile_mercado_db")
mycursor.execute("use chile_mercado_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="chile_mercado_db"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
link = "https://listado.mercadolibre.cl/tv#D[A:tv]"
is_scraped =0
# %%
def get_links(link):
    r = requests.get(link).text
    soup = BeautifulSoup(r, 'lxml')
    products = soup.find_all("li", class_ = "ui-search-layout__item shops__layout-item")
    for product in products:
        product_link = product.find("a").get("href")
        print(product_link)
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (product_link, is_scraped))
        chile_mercado_db.commit()
# %%
while True:
    try:
        r = requests.get(link).text
        soup = BeautifulSoup(r, 'lxml')
        next = soup.find("li", class_ = "andes-pagination__button andes-pagination__button--next shops__pagination-button")
        url = next.find("a").get("href")
        get_links(link)
        link = url
    except: break
# %%
