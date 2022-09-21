#%%
from ast import Continue
from statistics import mean
from time import sleep
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import mysql.connector
import pandas as pd

#%%

##create database
pricena_tv_saudi_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

##connect to db
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="pricena_tv_saudi_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor = pricena_tv_saudi_db.cursor(buffered=True)
mycursor.execute("DROP SCHEMA  IF EXISTS pricena_tv_saudi_db;")
mycursor.execute("CREATE DATABASE IF NOT EXISTS pricena_tv_saudi_db")
s = HTMLSession()

mycursor.execute("use pricena_tv_saudi_db")

mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_url VARCHAR(300) UNIQUE, is_scraped TINYINT)""")

s = HTMLSession()

#url = 'https://sa.pricena.com/en/tv-video/tv/page/5'
#%%
def get_product_links(page):
    url = f'https://sa.pricena.com/en/tv-video/tv/page/{page}'
    is_scraped = 0
    product_links= []
    r = s.get(url)
    products = r.html.find('div.item.desktop')
    for item in products:
        tv_url = item.find('a', first = True).attrs['href']
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_url, is_scraped))
        pricena_tv_saudi_db.commit()
        product_links.append(tv_url)
        if tv_url in product_links:
                continue
    return product_links


#%%
def get_avg_price(response):
    offer_prices = []
    offers = response.html.find('div[itemprop="offers"] div.price')
    for offer in offers:
        offer_price = offer.find('span.value', first = True).text.strip()
        offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c =='.')))
        offer_prices.append(offer_price)
        
    avg_price = mean(offer_prices)
    
    return avg_price


#%%
def get_specs(response):
    specs = []
    props = response.html.find('ul#properties', first = True)
    spec_list = props.find('li')
    #print(spec_list)
    for spec in spec_list:
        spec_value = spec.find('span[class="value"]', first = True).text
        spec_name = spec.find('span')[0].text
        spec_dict = {spec_name:spec_value}
        specs.append(spec_dict)

    return specs
# %%
def get_data(url):
    r = s.get(url)
    script = """
        () => {
                $(document).ready(function() {  
                    $("a.arrow").click();
                })
            }
            """
    r.html.render(scrolldown=5000, script = script, timeout = 20)
    title = r.html.find('h1[itemprop ="name"]', first = True).text.strip()
    price = r.html.find('div.price-value', first = True).text.strip()
    try:
        brand = r.html.find('span.brand', first = True).text.strip().replace("by ", "")
    except:
        brand = None
    number_of_offers = r.html.find('span.number', first = True).text.strip()
    currency = r.html.find('span.curr', first = True).text.strip()
    average_price = get_avg_price(r)
    specifications = get_specs(r)
    tv = {"title":title, 
        "price":price, 
        "brand":brand, 
        "number_of_offers":number_of_offers, 
        "currency":currency, 
        "average_price":average_price, 
        "specifications":specifications}
    print(title)
    
    return tv

#%%
for x in range(1, 100):
    get_product_links(x)

# %%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=pricena_tv_saudi_db)
tv_urls = []
for i in df_links['tv_url']:
    tv_urls.append(i)
for url in tv_urls:
    data = []
    data.append(get_data(url))
    df = pd.DataFrame.from_dict(data).astype("string")
    df.to_sql('data_table', engine, if_exists='append', index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_url = (%s)"
    tv_url = (url,)
    mycursor.execute(sql, tv_url)
    pricena_tv_saudi_db.commit()
# %%
