#%%
import httpx
import requests
from selectolax.parser import HTMLParser
import warnings
import mysql.connector
warnings.filterwarnings("ignore")

from fake_useragent import UserAgent

ua = UserAgent()
print(ua.random)
header = {'User-Agent':str(ua.random)}
url = "https://www.epey.com/kat/listele/"

#%%
epey_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = epey_tvs.cursor()
#mycursor.execute("DROP DATABASE IF EXISTS epey_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS epey_tvs")

#%%
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="epey_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use epey_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(500) UNIQUE, is_scraped TINYINT)""")

# %%
is_scraped = 0
for page in range(0, 187):
    payload = {"sayfa": page, 'kategori_id': 3, "cerez": "MTkzMjEr", }
    response = requests.post(url, headers=header, data=payload, verify=False)
    print(response.status_code)
    resp = HTMLParser(response.text)
    tv_links = resp.css("div[class = 'detay cell'] a")
    #print(len(tv_links))
    for link in tv_links:
        tv_link = link.attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        epey_tvs.commit()

# %%
