#%%
from fake_useragent import UserAgent
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy import engine
from statistics import mean
import time
import re
from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.by import By
import datetime
from selenium.webdriver.chrome.options import Options
import mysql.connector
from sqlalchemy import create_engine

#SELENIUM OPTIONS
options = Options()
options.add_argument("start-maximized")
options.add_argument('-headless')

ua = UserAgent()
headers = {'User-Agent':str(ua.random)}
driver = webdriver.Chrome(options=options)
#%%
##create database
mercado_db_guatemala = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = mercado_db_guatemala.cursor()

# Credentials to database connection
hostname="localhost"
dbname="mercado_db_guatemala"
uname="root"
pwd="4156"

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use mercado_db_guatemala")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(category varchar(200), country_code varchar(20),name varchar(200), specifications MEDIUMTEXT, original_price varchar(100), offer_price varchar(200), discount_percentage varchar(200), start varchar(200), \
                    quantity_available varchar(200), reviews varchar(100), rating varchar(100), scrape_link varchar(200) PRIMARY KEY, date_scraped varchar(100))""")

#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=mercado_db_guatemala)

links = []
for i in df_links.link:
    links.append(i)

#%%
len(links)

#%%
def get_prices(soup_object):
    try: 
        offer_price = soup_object.find("div", class_ = "ui-pdp-price__second-line")
        offer_price = offer_price.find("span", class_ = "andes-visually-hidden").text
    except:
        price_link = soup_object.find("button", class_ = "andes-button andes-spinner__icon-base andes-button--loud").get("formaction")
        req = requests.get(price_link).text
        sup = BeautifulSoup(req, features='lxml')
        offer_price = sup.find("span", class_ = "andes-money-amount__fraction").text.strip()
    return offer_price

#%%
def get_specs(tables):
        column_names = []
        dt = []
        for table in tables:
            for row in table.find_all('th'):
                name = row.get_text()
                column_names.append(name)

            for row in table.find_all('td'):
                name = row.get_text()
                dt.append(name)
        
        specs = {column_names[i]: dt[i] for i in range(len(column_names))}
        return specs


#%%
def get_data(link):
    from datetime import datetime
    driver.get(link)
    driver.implicitly_wait(2.5)
    scheight = .1
    while scheight < 9.9:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .008
    r = requests.get(link, headers=headers).text
    hun = BeautifulSoup(driver.page_source, features='lxml')
     
    try:
        currency = hun.find("span", class_ = "andes-money-amount__currency-symbol").text.strip()
    except:
        currency = None
    
    try:
        original_price = hun.find("s", class_ = "andes-money-amount ui-pdp-price__part ui-pdp-price__original-value andes-money-amount--previous andes-money-amount--cents-superscript andes-money-amount--compact")
        original_price = original_price.find("span", class_ = "andes-visually-hidden").text
    except:
        original_price = None


    try:
        offer_price = get_prices(hun)
    except:
        offer_price = None
        
    try:
        discount_percentage = hun.find("span",{"class":"andes-money-amount__discount"}).text.replace('\n',"")
    except:
        discount_percentage = None
        
    try:
        sales = hun.find("span",{"class":"ui-pdp-subtitle"}).text.strip()
    except:
        sales = None
    
    try:
        quantity_available = hun.find("span", {"class":"ui-pdp-buybox__quantity__available"}).text.strip()
    except:
        quantity_available = None
        
    try:
        reviews = hun.find("span",{"class":"ui-pdp-review__amount"}).text.replace('\n',"")
    except:
        reviews = None
    try:
        section = hun.find_all("div", class_ = "ui-vpp-striped-specs__table")
        tables = []
        for sect in section:
            tables.append(sect.find("table"))
        #tables = hun.find_all("tbody", class_ = "andes-table__body")
        specifications = get_specs(tables)
    except:
        specifications = None

    try:
        name=hun.find("h1",{"class":"ui-pdp-title"}).text.replace('\n',"")
    except:
        name=None

    print(name)
    
    try:
        category = "Televisores"
    except:
        category = None
    
    try:
        rating = hun.find("p", class_ = "ui-review-capability__rating__average ui-review-capability__rating__average--desktop").text.strip()
    except:
        rating = None
    try:
        state = hun.find("span", class_ = "ui-pdp-buybox__quantity__available").text.strip()
    except:
        state = None
        
    try:
        country_code = "GT"
    except:
        country_code = None
    try:
        scrape_link = link
        
    except:
        scrape_link = None
    
    try:
        now = datetime.now()
        date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")
    except:
        date_scraped = None
    '''
    engine.execute("""INSERT IGNORE INTO programs VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                   (name, country_code, country_code, rating, category, currency, original_price, offer_price,  discount_percentage, sales, quantity_available, state, specifications, scrape_link, date_scraped))
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE item_link = (%s)"
    item_link = (link,)
    engine.execute(sql, item_link)
    '''
    print(specifications)

    tv = {"name":name,   "Country Code": country_code, "rating":rating, "category":category,"Currency":currency, "original_price":original_price, "offer_price":offer_price,\
         "discount_percentage":discount_percentage, "sales":sales, "quantity_available":quantity_available, "state":state,"reviews":reviews, "specifications":specifications, "scrape_link":scrape_link, "date_scraped":date_scraped}
    print(tv)
    return tv

#%%
for link in links:
    data = []
    print(link)
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE link = (%s)"
    link = (link,)
    mycursor.execute(sql, link)
    mercado_db_guatemala.commit()


#%%
df = pd.read_sql('SELECT * FROM data_table', con=mercado_db_guatemala)
none_links = []
for link in df[(df['name'] == 'None') | (df['specifications'] == '{}')]['scrape_link']:
    none_links.append(link)

#%%
##removes where the links wer empty before scraping to avoid duplication
for link in none_links:
    sql = f"DELETE FROM data_table WHERE scrape_link = '{link}';"
    mycursor.execute(sql)
    mercado_db_guatemala.commit()
    
#%%
len(none_links)
#%%
for link in none_links:
    print(link)
    data = []
    time.sleep(2)
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE link = (%s)"
    link = (link,)
    mycursor.execute(sql, link)
    mercado_db_guatemala.commit()
    time.sleep(1)

#%%
df = pd.read_sql('SELECT * FROM data_table', con=mercado_db_guatemala)
pd.DataFrame(df['offer_price'].str.split().values.tolist())[[1]]
#df['offer_price'].str.replace(r"[^a-z]+", "")
#%%
##Feature Engineering
df['discount_percentage'] = df['discount_percentage'].str.extract('(\d+)', expand=False)
df['sales'] = df['sales'].str.extract('(\d+)', expand=False)
df['reviews'] = df['reviews'].str.extract('(\d+)', expand=False)
df['quantity_available'] = pd.DataFrame(df['offer_price'].str.split().values.tolist())[[0]]
df['Currency'] = pd.DataFrame(df['offer_price'].str.split().values.tolist())[[1]]
df['offer_price'] = df['offer_price'].str.extract('(\d+)', expand=False)
df['original_price'] = df['original_price'].str.extract('(\d+)', expand=False)

#%%
df['quantity_available'] = df['quantity_available'].fillna(1) #Where quantity is empty replace with 1

#%%
df['specifications'] =df['specifications'].apply(lambda x: dict(eval(x)))
spec_df = df['specifications'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df.drop(['specifications'], axis = 1,  inplace=True)

#%%
df_l  = pd.concat([df[['Country Code', 'name', 'quantity_available', 'state', 'Currency', 'original_price', 'offer_price', 'sales', 'category', 'date_scraped', 'scrape_link']], spec_df.reindex(df.index)], axis=1)
df_long = df_l.set_index(['Country Code', 'Marca', 'Modelo', 'Modelo alfanumérico', 'category', 'name', 'quantity_available',  'Currency', 'original_price','offer_price','sales','date_scraped', 'scrape_link']).stack().reset_index()
df_long.head()
df_long.rename(columns = {'level_14':'Specification Name', 0:'Specification Value'}, inplace=True)
#%%
df_long.to_csv("tv_data_long.CSV")
df.to_csv('tv_data.csv')

# %%
