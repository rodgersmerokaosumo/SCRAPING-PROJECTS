#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
from statistics import mean
import time
from datetime import datetime
import mysql.connector
import pymysql
from sqlalchemy import create_engine


headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

#%%
##create database
jumia_algeria_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = jumia_algeria_db.cursor()
mycursor.execute("DROP DATABASE IF EXISTS jumia_algeria_db")
mycursor.execute("CREATE DATABASE IF NOT EXISTS jumia_algeria_db")
mycursor.execute("use jumia_algeria_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="jumia_algeria_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
productlinks = []
is_scraped = 0

#%%
url = "https://www.jumia.dz/tvs/"
base_url = "https://www.jumia.dz"
pages = []
pages.append(url)

while True:
    req = requests.get(url).text
    soup = BeautifulSoup(req, 'lxml')
    try:
      url = base_url + soup.find("a", {"aria-label":"Page suivante"}).get("href")
      print(url)
      pages.append(url)
    except:
        break

#%%
for page in pages:
    r = requests.get(page)
    soup = BeautifulSoup(r.content, 'lxml')
    productlist = soup.find('div', class_ = '-paxs row _no-g _4cl-3cm-shs')
    productlist = productlist.find_all('article', class_ = 'prd _fb col c-prd')

    for product in productlist:
        prod_link = product.find("a", class_ = "core")
        tv_link = base_url+prod_link['href']
        engine.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        productlinks.append(tv_link)
        print(f"{tv_link} : is scraped.")
# %%
