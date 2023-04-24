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
#options.add_argument('-headless')

#%%
##create database
ceneo_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)
mycursor = ceneo_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS ceneo_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS ceneo_tvs")
mycursor.execute("use ceneo_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) unique,is_Scraped  TINYINT)""")

#%%
# Credentials to database connection
hostname="localhost"
dbname="ceneo_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
is_scraped = 0

#%%
driver = webdriver.Chrome(options=options)
url = "https://www.ceneo.pl/Telewizory"
base_url = "https://www.ceneo.pl"
#%%
tv_links = []
while True:
    try:
        driver.get(url)
        driver.implicitly_wait(2.5)
        scheight = .1
        while scheight < 9.9:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
            scheight += .008
        time.sleep(2)
        resp = HTMLParser(driver.page_source)
        links = resp.css("a[class = 'go-to-product js_conv js_clickHash js_seoUrl']")
        for link in links:
            tv_link = base_url+link.attrs["href"]
            mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
            tv_links.append(tv_link)
        next_page = base_url+resp.css_first("a[class= 'pagination__item pagination__next']").attrs["href"]
        url = next_page
        print(next_page)
    except:break