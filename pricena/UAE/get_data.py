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
uae_db= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = uae_db.cursor()

mycursor.execute("use uae_db")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="uae_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
link = "https://ae.pricena.com/en/product/samsung-smart-tv-neo-qled-8k-qn800b-65-inch-sa-price-in-dubai-uae-133462014"

#%%
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)
#%%
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
def get_offers(soup):
    prices = []
    offers = soup.find("div", {"id":"comparison"})
    offers = offers.find_all("div", {"itemprop":"offers"})
    for offer in offers:
        offer = offer.find("div", class_ = "price")
        offer = offer.find("span", class_ = "value").text.strip()
        offer = float(''.join(c for c in offer if (c.isdigit() or c =='.')))
        prices.append(offer)
    return prices
#%%
def get_specs(soup):
    specifications = []
    spec_names = []
    spec_vals = []
    specs= soup.find("div", {"class":"techspecs-block"})
    specs = specs.find("ul", {"id":"properties"})
    properties  = specs.find_all("li")
    for property in properties:
        spec_name = property.find("span", class_="").text.strip()
        spec_value = property.find("span", class_="value").text.strip()
        spec_names.append(spec_name)
        spec_vals.append(spec_value)
    specs = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    return specs
#%%
def get_data(link):
    driver.get(link)
    driver.implicitly_wait(5)
    total_height = int(driver.execute_script("return document.body.scrollHeight"))
    for i in range(1, total_height, 5):
        driver.execute_script("window.scrollTo(0, {});".format(i))
    category = "TV"
    time.sleep(3)
    try:
        myLink = driver.find_element(By.CSS_SELECTOR, 'div#linkShowAllProp')
        myLink.click()
    except:
        pass

    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        currency = soup.find("span", class_ = "curr").text.strip()
    except:
        currency = "AED"
    try:
        title = soup.find("h1").text.strip()
    except:
        title = None
    try:
        brand = soup.find("span", class_ = "brand")
        brand = brand.find("a").text.strip()
    except:
        brand = None
    try:
        best_price = soup.find("span", class_ = "lowPrice").text.strip()
    except:
        best_price = None
    country = "UAE"
    try:
        specs = get_specs(soup)
    except:
        specs = None
    try:
        offers = len(get_offers(soup))
        avg_price  = mean(get_offers(soup))
    except:
        offers = 1
        avg_price = best_price

    now = datetime.datetime.now()
    date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")
    country = "UAE"

    tv = {
        "country": country,
        "category":category,
        "currency":currency,
        "title":title,
        "brand":brand,
        "best_price":best_price,
        "specifications":specs,
        "offers":offers,
        "avg_price":avg_price,
        "scrape_link":link,
        "date_scraped":date_scraped
    }
    #print(tv)
    return tv


# %%
#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=uae_db)
tv_links = []
for i in df_links['tv_link']:
    tv_links.append(i)
# %%
tv_links
#%%
count = 0
for link in tv_links:
        data = []
        print(link)
        #print(len(data))
        data.append(get_data(link))
        #print(dat)
        df = pd.DataFrame.from_dict(data).astype(str)
        df.to_sql('data_table', engine, if_exists='append', index=False, schema='uae_db')
        sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
        tv_link = (link,)
        mycursor.execute(sql, tv_link)
        uae_db.commit()
        count = count + 1
        print(count)
# %%
df = pd.read_sql("SELECT * FROM data_table where best_price != 'None'", con=uae_db)
df["specifications"] = df["specifications"].apply(lambda x : dict(eval(x)))
df2 = df["specifications"].apply(pd.Series)
df = pd.concat([df, df2], axis=1).drop('specifications', axis=1).astype(str)
df_long = df.set_index(['country',  'brand', 'Model#', 'title', 'offers', 'avg_price', 'currency', 'Date added', 'category' , 'date_scraped','scrape_link']).stack().reset_index()
df_long.to_csv("pricena_uae_data.csv")


# %%
