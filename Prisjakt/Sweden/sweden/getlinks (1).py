#%%
import httpx
from selectolax.parser import HTMLParser
import mysql.connector
from sqlalchemy import create_engine


#%%
url = "https://www.prisjakt.nu/c/tv"
base_url = 'https://www.prisjakt.nu'

#%%
##create database
prisjakt_sweden_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  autocommit = True
)

mycursor = prisjakt_sweden_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS prisjakt_sweden_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS prisjakt_sweden_tvs")
mycursor.execute("use prisjakt_sweden_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) unique,is_Scraped  TINYINT)""")

#%%
# Credentials to database connection
hostname="localhost"
dbname="prisjakt_sweden_tvs"
uname="root"
pwd="root"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
def get_links(url):
    is_scraped = 0
    req = httpx.get(url)
    resp = HTMLParser(req.text)
    products = resp.css("article[data-test = 'ProductGridCard']")
    for product in products:
        tv_link = base_url + product.css_first("a[data-test = 'InternalLink']").attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
    next_page = base_url + resp.css_first("a[aria-label='Visa nästa']").attrs["href"]
    print(next_page)
    return next_page

#%%
while True:
    try:
        url = get_links(url)
    except:
        break
# %%
