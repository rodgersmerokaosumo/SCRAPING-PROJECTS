#%%
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

#SELENIUM OPTIONS
options = Options()
options.add_argument("start-maximized")
#options.add_argument('-headless')

#%%
##create database
sports_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True,
    auth_plugin = 'mysql_native_password',
)

mycursor = sports_db.cursor()

#%%
# Credentials to database connection
hostname="localhost"
dbname="sports_db"
uname="root"
pwd="root"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("CREATE DATABASE  IF NOT EXISTS sports_db")
mycursor.execute("use sports_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS item_links(item_info varchar(200), item_name varchar(200), program_date varchar(50),item_time varchar(200), item_rebroadcast varchar(200), item_channel varchar(200), \
                    item_link varchar(200) UNIQUE, is_scraped TINYINT, date_scraped varchar(100))""")

#%%
driver = webdriver.Chrome(options=options)
#%%
def get_item_data(soup):
    '''
    driver.get(url)
    time.sleep(5)
    driver.implicitly_wait(5)
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 5):
        driver.execute_script("window.scrollTo(0, {});".format(i))
    soup = BeautifulSoup(driver.page_source, 'lxml')
    '''
    start = soup.find_all("h3", class_="entete_items text-left")[1]
    program_date = start.text.replace('Programmes  ', '')
    is_scraped = 0
    item_list = []
    for tr in start.find_next_siblings("div"):
        # get all divs with a desired class
        try:
            item = tr.find("h2", class_ = "item_title")
        except:
            item = None
        try:
            item_info = tr.find("small").text
        except:
            item_info = None
        try:
            item_name = item.text.strip()
        except:
            item_name = None
        try:
            item_time = tr.find("div", class_ = "col-8 text-right").text.strip()
        except:
            item_time = None
        try:
            item_rebroadcast = tr.find("div", class_ = "col-4 align-self-center").text.strip()
        except:
            item_rebroadcast = None
        try:
            item_link = item.find("a")
            item_link = item_link['href']
        except:
            item_link = None
        try:
            item_channel = tr.find_all("div", class_ = "col-2 col-md-1 align-self-center")[1]
            item_channel = item_channel.find("img")
            item_channel = item_channel["alt"]
        except:
            item_channel = None
        now = datetime.datetime.now()
        date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")
        engine.execute("""INSERT IGNORE INTO item_links VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)""", (item_info, item_name, program_date,item_time, item_rebroadcast, item_channel, item_link, is_scraped, date_scraped))

        item_dict = {
            "item_info":item_info,
            "item_name":item_name,
            "program_date":program_date,
            "item_time":item_time,
            "item_rebroadcast":item_rebroadcast,
            "item_channel":item_channel,
            "item_link":item_link
        }
        print(item_dict)
        item_list.append(item_dict)
    return item_list


#%%
base_url = "https://tv-sports.fr/"
url = base_url

#%%
next_page_urls = []
counter  = 0
while counter <9:
    driver.get(url)
    time.sleep(5)
    driver.implicitly_wait(2)
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 5):
        driver.execute_script("window.scrollTo(0, {});".format(i))
    soup = BeautifulSoup(driver.page_source, 'lxml')
    get_item_data(soup)
    counter = counter +1
    try:
        url = soup.find("button", text="Jour suivant »").parent['href']
        next_page_urls.append(url)
    except:
        break
#%%
url = base_url
#Previous days
while True:
    driver.get(url)
    time.sleep(5)
    driver.implicitly_wait(2)
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 5):
        driver.execute_script("window.scrollTo(0, {});".format(i))
    try:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        body = soup.find_all("h3", class_="entete_items text-left")[1]
        if body is not None:
            get_item_data(soup)
            url = soup.find("button", text="« Jour précédent").parent['href']

            if url not in next_page_urls:
                next_page_urls.append(url)
        else:
            break
    except:
        break
#%%
