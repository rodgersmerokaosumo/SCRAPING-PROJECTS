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

#SELENIUM OPTIONS
options = Options()
options.add_argument('--ignore-certificate-errors-spki-list')
options.add_argument("start-maximized")
options.add_argument("window-size=1200x600")
#options.add_experimental_option('excludeSwitches', ['enable-logging'])
options.headless = True

#%%
##create database
sports_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = sports_db.cursor()

#%%
# Credentials to database connection
hostname="localhost"
dbname="sports_db"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use sports_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS programs(program_name varchar(200), program_duration varchar(200), program_rebroadcast varchar(200), program_start_time varchar(200), \
                    link varchar(200) UNIQUE, date_scraped varchar(100))""")

#%%
df_links = pd.read_sql('SELECT * FROM item_links WHERE is_scraped = 0', con=engine)

links = []
for i in df_links.item_link:
    links.append(i)

#%%
def get_program_data(link, driver):
    driver.get(link)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        program_name = soup.find("h1", class_="page-title text-left").text
    except:
        program_name = None
    try:
        program_duration = soup.find("small", class_="badge badge-light").text
    except:
        program_duration = None
    try:
        spans = soup.find_all("div", class_="col-9 justify-content-center align-self-center")[0].findAll("span",
                                                                                                         recursive=False)
        program_rebroadcast = spans[0].text
        program_start_time = spans[1].text
    except:
        program_rebroadcast = None
        program_start_time = None
    now = datetime.datetime.now()
    date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")
    engine.execute("""INSERT IGNORE INTO programs VALUES(%s, %s, %s, %s, %s, %s)""",
                   (program_name, program_duration, program_rebroadcast, program_start_time, link, date_scraped))
    sql = "UPDATE item_links SET is_scraped = 1 WHERE item_link = (%s)"
    item_link = (link,)
    engine.execute(sql, item_link)

    program_dict = {
        "program_name": program_name,
        "program_duration": program_duration,
        " program_rebroadcast": program_rebroadcast,
        "program_start_time": program_start_time,
        "program_link": link,
        "date_scraped": date_scraped

    }
    print(program_dict)
    return program_dict

#%%
data = []
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
for link in links:
    data.append(get_program_data(link, driver))

#%%
df_items = pd.read_sql("item_links", con = engine)
df_programs = pd.read_sql("programs", con = engine)

#%%
result = pd.concat([df_items, df_programs], axis=1)

#%%
result.columns

#%%
df = result[['item_channel','program_date', 'item_name', 'item_info', 'program_start_time', 'program_duration', 'program_rebroadcast', 'link']]

df.to_csv('SAMPLE.CSV')