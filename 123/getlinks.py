#%%
import requests
from selectolax.parser import HTMLParser
import warnings
import mysql.connector
import pymysql
warnings.filterwarnings("ignore")

#%%
URL = "https://www.123comparer.be/Televiseur/"
base_url = "https://www.123comparer.be"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.62',
'Accept-Language': 'en-US,en;q=0.9'}


#%%
belgium_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = belgium_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS belgium_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS belgium_tvs")

#%%
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="belgium_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use belgium_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(500) UNIQUE, is_scraped TINYINT)""")

#%%
product_links = []
is_scraped = 0
for page in range(0, 70):
    payload = {'p': page}
    response = requests.post(URL, headers=headers, data=payload, verify=False)
    resp = HTMLParser(response.text)
    print(response.status_code)
    links = resp.css("p[class = 'oldH3'] a")
    print(page)
    for link in links:
        tv_link = base_url + link.attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        belgium_tvs.commit()

# %%
