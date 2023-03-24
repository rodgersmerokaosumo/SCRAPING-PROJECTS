#%%
from statistics import mean
import mysql.connector as mysql
import time
import requests
import pandas as pd
import datetime
from selenium.webdriver.common.action_chains import ActionChains
import mysql.connector
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException


#SELENIUM OPTIONS
options = Options()
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument("start-maximized")
#options.add_argument("window-size=1200x600")
#options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.add_argument('-headless')


#%%
##create database
saudi_db= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = saudi_db.cursor()

mycursor.execute("DROP DATABASE IF EXISTS saudi_db")
mycursor.execute("CREATE DATABASE IF NOT EXISTS saudi_db")
mycursor.execute("use saudi_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")
mycursor.execute("use saudi_db")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="saudi_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))
# %%
def pageBottom(driver):
    bottom=False
    a=0
    while not bottom:
        new_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script(f"window.scrollTo(0, {a});")
        if a > new_height:
            bottom=True
        a+=5

#%%
link = "https://sa.pricena.com/en/tv-video/tv"
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
driver.get(link)
pageBottom(driver)
# %%
page = 1
is_scraped = 0
pages = []
while page <=96:
        driver.implicitly_wait(5)
        #driver.execute_script("window.scrollBy(0,3000)","")
        #pageBottom(driver)
        myLink = driver.find_element(By.PARTIAL_LINK_TEXT, 'Show More')
        print(myLink.get_attribute("href"))
        #pageBottom(driver)
        if len(pages) >0:
            if myLink.get_attribute("href") == pages[-1]:
                break
        pages.append(myLink.get_attribute("href"))
        myLink.click()
        page = page + 1
# %%
soup = BeautifulSoup(driver.page_source, 'lxml')
products = soup.find_all("div", {"class":"item desktop"})
for product in products:
     link = product.find("a").get("href")
     mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (link, is_scraped))
     saudi_db.commit()
     print(link)
#%%
print(len(products))
# %%
