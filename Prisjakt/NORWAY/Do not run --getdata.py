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
#options.add_argument('-headless')


#%%
##create database
prisjakt_norway_tvs= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = prisjakt_norway_tvs.cursor()

mycursor.execute("use prisjakt_norway_tvs")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="prisjakt_norway_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%

#%%
def get_specs(soup):
    prop_names = []
    prop_vals = []
    sections = soup.find_all("section", {"role":"list"})
    for section in sections:
        listitems = section.find_all("div", {"role":"listitem"})
        for item in listitems:
            col_names = item.find_all("span", class_ = "Text--1ka53sf dsObrg bodysmalltext PropertyName-sc-1jnk5ag-5 hEdIXF")
            for name in col_names:
                spec_name = name.text.strip()
                prop_names.append(spec_name)
            col_vals = item.find_all("span", class_ = "Text--1ka53sf jytHci bodysmalltext PropertyValue-sc-1jnk5ag-6 etcKHO")
            for val in col_vals:
                spec_val = val.text.strip()
                prop_vals.append(spec_val)
    specs = {prop_names[i]: prop_vals[i] for i in range(len(prop_names))}
    print(specs)
    return specs

#%%
def get_offers(soup):
    offers = []
    prices = soup.find("ul", class_ = "PriceList-sc-wkzg9v-0 fbrkVc")
    prices = soup.findAll(attrs= {"data-test":"PriceLabel"})
    for price in prices:
        try:
            offer_price = price.text.strip()
            offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c =='.')))
            offers.append(offer_price)
        except:
            pass
    #print(offers)
    return offers

#%%
def pageBottom(driver):
    bottom=False
    a=0
    while not bottom:
        new_height = driver.execute_script("return document.body.scrollHeight")
        driver.execute_script(f"window.scrollTo(0, {a});")
        if a > new_height:
            bottom=True

#%%
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

#%%
def get_data(url):
    driver.refresh()
    driver.get(url)
    time.sleep(5)
    pageBottom(driver)
    time.sleep(2)
    
    try:
        cookies = driver.find_element(By.CSS_SELECTOR, "button#AcceptButton-cookie-banner")
        cookies.click()
    except NoSuchElementException:
        pass
    try:
        more  = driver.find_element(By.CSS_SELECTOR, "button.BaseButton--303e6a.iQRQdv.textbutton")
        more.click()
    except:
        pass
    try:
        specs = driver.find_element(By.XPATH, '//*[@id="#properties"]/div/section/section/div[1]/div[1]/div[2]/section[3]')
    except NoSuchElementException:
        pass
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        category = soup.find_all("span", {"class":"CrumbItem--1n9dlop bhJokh"})[-1].text.strip()
    except:
        category = "TV"
    try:
        title = soup.find("h1").text.strip()
    except:
        title =  None
    try:
        avg_price = mean(get_offers(soup))
        no_offers = len(get_offers(soup))
        print(no_offers, avg_price)
    except:
        avg_price, no_offers = None

    try:
        specs = get_specs(soup)
    except:
        specs = None
    #print(offer_list)

    country = "DK"

    currency = "SEK"

    scrape_link = url

    now = datetime.datetime.now()
    date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")

    #scrape_datetime = scrape_time.strftime("%d/%m/%Y %H:%M:%S")

    tv = {"Category":category,
        "Title":title,
          "Offers":no_offers,
          "avg_price":avg_price,
          "Specifications":specs,
          "Country": country,
          "Currency": currency,
          "Scrape_link":scrape_link,
          "Scrape_time":date_scraped}
    return tv

#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)
tv_links = []
for i in df_links['tv_link']:
    tv_links.append(i)

#%%
len(tv_links)
#%%
driver.get(tv_links[0] +"#properties")
time.sleep(2)
soup = BeautifulSoup(driver.page_source, 'lxml')
get_specs(soup)



#%%
for link in tv_links[:50]:
    data = []
    print(link)
    data.append(get_data(link+"#properties"))
    df = pd.DataFrame.from_dict(data).astype("string")
    df.to_sql('data_table', engine, if_exists='append', index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    engine.execute(sql, tv_link)

#%%
import pandas as pd
df = pd.read_sql('SELECT * FROM data_table', con=engine)
#df = df.fillna("NOT AVAILABLE")
df['Specifications'] =df['Specifications'].apply(lambda x: dict(eval(x)))
spec_df = df['Specifications'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df.drop(["Specifications"], axis = 1,  inplace=True)

#%%
df_long = df.set_index(['Country', 'Category','Title', 'Mærke', 'avg_price', 'Offers', 'Currency', 'Scrape_link', 'Scrape_time']).stack().reset_index()
df_long.to_sql('cleaned_data', engine, if_exists='replace', index=False)
df_long.to_csv('sample.csv')
#%%
