#%%
from statistics import mean
import time
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from selectolax.parser import HTMLParser
from selenium.webdriver.common.by import By
import datetime
from selenium.webdriver.chrome.options import Options
import mysql.connector
from sqlalchemy import create_engine
import re

#SELENIUM OPTIONS
options = Options()
options.add_argument("start-maximized")
#options.add_argument('-headless')

#%%
##create database
tvsports_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)
mycursor = tvsports_db.cursor()

#%%
# Credentials to database connection
hostname="localhost"
dbname="tvsports_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor.execute("use tvsports_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS items_table(item_name varchar(200), channel varchar(200), item_rebroadcast varchar(200), item_time varchar(200), item_link varchar(200))""")

#%%
driver = webdriver.Chrome(options=options)
url = "https://tv-sports.fr/tennis-open-de-munich-2023-tv-x903553"

#%%
def get_items(url):
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3.5);window.scrollTo(0, document.body.scrollHeight/3.7);")
    time.sleep(2)
    resp = BeautifulSoup(driver.page_source, 'html.parser')
    items_list = []
    items = resp.find("div", class_ = "col-md-9")
    try:
        item_name = resp.find("h5", class_ = "headline").text.strip()
    except:item_name = None
    trs = items.find_all("div", class_=lambda x: x and x.startswith('bg-light row border-bottom'))
    for tr in trs:
        try:
            channel = tr.find("div", class_ = "col-3 text-center justify-content-center align-self-center")
            channel = channel.find("img").get("alt")
        except:channel = None
        try:
            item_rebroadcast = tr.find("span", class_=lambda x: x and x.startswith('badge badge-')).text.strip()
        except: item_rebroadcast = None
        try:
            item_time = tr.find("span", {"style":"font-size:1.15rem;"}).text.strip() 
        except:item_time = None
        item= {
            "item_name":item_name,
            "channel":channel,
            "item_rebroadcast":item_rebroadcast,
            "item_time":item_time,
            "item_link":url
        }
        items_list.append(item)

    mycursor.executemany("""
        INSERT IGNORE INTO items_table (item_name, channel, item_rebroadcast, item_time, item_link)
        VALUES (%(item_name)s, %(channel)s, %(item_rebroadcast)s, %(item_time)s, %(item_link)s)""",items_list)
    
    print(items_list)
    return items_list


#%%
df_p= pd.read_sql('SELECT * FROM programs where is_scraped = 0;', con=engine)
item_links = []

#%%
for i in df_p['prog_link']:
    item_links.append(i)

# %%
for link in item_links:
    get_items(link)
    sql = "UPDATE programs SET is_scraped = 1 WHERE prog_link = (%s)"
    link = (link,)
    mycursor.execute(sql, link)

#%%
df = pd.read_sql("""SELECT * FROM items_table INNER JOIN programs ON  items_table.item_link = programs.prog_link;""", con=engine)
df.drop(["item_link"], axis=1, inplace=True)
df.to_csv("tv_data.csv")
# %%
