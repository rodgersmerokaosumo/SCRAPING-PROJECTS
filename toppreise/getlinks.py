#%%
from statistics import mean
import time
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selectolax.parser import HTMLParser
import datetime
from selenium.webdriver.chrome.options import Options
import mysql.connector
from sqlalchemy import create_engine

#SELENIUM OPTIONS
options = Options()
options.add_argument("start-maximized")
options.add_argument('-headless')

#%%
##create database
toppreise_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)
mycursor = toppreise_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS toppreise_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS toppreise_tvs")
mycursor.execute("use toppreise_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) unique,is_Scraped  TINYINT)""")

#%%
# Credentials to database connection
hostname="localhost"
dbname="toppreise_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
is_scraped = 0

#%%
#driver = webdriver.Chrome(options=options)
url = "https://www.toppreise.ch/produktsuche/TV-Video/TV-Geraete-Zubehoer/TV-Geraete-c986"
base_url = "https://www.toppreise.ch"



#%%
tv_links = []
while True:
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        button = driver.find_element(By.CLASS_NAME, "f_submit.btnInverted")
        button.click()

        driver.implicitly_wait(2.5)
        btns = driver.find_elements(By.CLASS_NAME, "btn.f_serinfo")
        for btn in btns:
            btn.click()
            time.sleep(5)
        resp = HTMLParser(driver.page_source)
        links = []
        chunks = resp.css("div.Plugin_ProductCollItem.mixedBrowsingList.container  div.row div.col div.col-12.f_item")
        for chunk in chunks:
            links.append(chunk.css_first("a"))
        for link in links:
            tv_link = base_url+link.attrs["href"]
            mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
            tv_links.append(tv_link)
        next_page = base_url+resp.css_first("a.col-auto.f_pagination.next").attrs["href"]
        url = next_page
        print(next_page)
        driver.close()
    except:break
    
#%%