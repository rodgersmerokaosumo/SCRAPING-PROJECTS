#%%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector as mysql
from sqlalchemy import create_engine

#%%
##create database
prisjakt_denmark_tvs = mysql.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = prisjakt_denmark_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS prisjakt_denmark_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS prisjakt_denmark_tvs")
mycursor.execute("use prisjakt_denmark_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) unique,is_Scraped  TINYINT)""")

#%%
# Credentials to database connection
hostname="localhost"
dbname="prisjakt_denmark_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
is_scraped = 0
base_url = "https://prisjagt.dk"

#%%
url = "https://prisjagt.dk/c/tv"
def get_links(link, links):
    k = requests.get(link).text
    soup = BeautifulSoup(k, 'html.parser')
    items = soup.find_all("li", {"data-test":"ProductGridCard"})
    for item in items:
        link = base_url + item.find("a", {"data-test":"InternalLink"}).get("href")
        engine.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (link, is_scraped))
        links.append(link)
        print(link)

# %%
page_links = []
for page in range(0, 38):
    link = f"https://prisjagt.dk/c/tv?offset={page*44}"
    page_links.append(link)
#%%
page_links[9]


#%%
tv_links = []
for link in page_links:
    get_links(link, tv_links)

# %%
print(len(tv_links))
# %%
