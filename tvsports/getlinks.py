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
#%%
mycursor.execute("DROP DATABASE IF EXISTS tvsports_db")
mycursor.execute("CREATE DATABASE IF NOT EXISTS tvsports_db")
mycursor.execute("use tvsports_db")
mycursor.execute("""DROP TABLE IF EXISTS programs""")
mycursor.execute("""CREATE TABLE IF NOT EXISTS programs(prog_date varchar(200), prog_name varchar(200), prog_link varchar(200) UNIQUE, sport_info varchar(200), prog_rebroadcast varchar(200), prog_time varchar(200), is_scraped TINYINT)""")
#%%
is_scraped = 0

#%%
driver = webdriver.Chrome(options=options)
url = "https://tv-sports.fr"
is_scraped= 0
#%%
def get_data(url):
    programs_list= []
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3.5);window.scrollTo(0, document.body.scrollHeight/3.7);")
    time.sleep(2)
    resp = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        prog_date = resp.find("a", {"id":"navbarDropdownJours"}).text.strip()
    except: prog_date = "Date"
    h3s = resp.find_all("h3", class_="entete_items text-left")[1]
    for tr in h3s.find_next_siblings("div"):
        try:
            prog_name = tr.find("h2", class_ = "item_title").text.strip()
        except:prog_name = None
        try:
            prog_link = tr.find("h2", class_ = "item_title")
            prog_link = prog_link.find("a").get("href")
        except:prog_link = None
        try:sport_info =  tr.find("small").text
        except:sport_info = None
        try:prog_time = tr.find("div", class_= "col-8 text-right").text
        except:prog_time = None
        try:prog_rebroadcast = tr.find("div", class_= "col-4 align-self-center").text
        except:prog_rebroadcast = None

        program = {
        "prog_date":prog_date,
            "prog_name":prog_name,
            "prog_link":prog_link,
            "sport_info":sport_info,
            "prog_time":prog_time,
            "prog_rebroadcast":prog_rebroadcast, 
            "is_scraped":is_scraped
        }
        programs_list.append(program)
    next_page = resp.find("button", text="Jour suivant »").parent['href']
    prev_page = resp.find("button", text="« Jour précédent").parent['href']

    
    print(programs_list)

    mycursor.executemany("""
    INSERT IGNORE INTO programs (prog_date, prog_name, prog_link, sport_info, prog_time, prog_rebroadcast, is_scraped)
    VALUES (%(prog_date)s, %(prog_name)s, %(prog_link)s, %(sport_info)s, %(prog_time)s, %(prog_rebroadcast)s, %(is_scraped)s)""",programs_list)
    
    return next_page, prev_page


# %%
counter = 0
while counter <9:
    try:
        url = get_data(url)[0]
        counter +1
    except:
        break
# %%
url = "https://tv-sports.fr"
while True:
    try:
        url = get_data(url)[1]
        counter +1
    except:break
# %%
