#%%
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from statistics import mean
import time
from datetime import datetime
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}
import mysql.connector
import pymysql
from sqlalchemy import create_engine

headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

url = "https://www.jumia.com.ng/televisions/"
base_url = "https://www.jumia.com.ng"

#%%
##create database
jumia_nigeria_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)

mycursor = jumia_nigeria_db.cursor()

mycursor.execute("use jumia_nigeria_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="jumia_nigeria_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%

df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)

links = []
for i in df_links.tv_link:
    links.append(i)

#%%
len(df_links)

#%%
def offers(soup_object, prod_price):
    offers = []
    offers.append(prod_price)
    othersellerslink = soup_object.find_all("a", class_ = "btn _def _ti -mhs -fsh0")[0]
    othersellerslink  = base_url + othersellerslink ["href"]
    r_othersellers= requests.get(othersellerslink)
    soup_othersellers = BeautifulSoup(r_othersellers.content, 'lxml')
    othersellers = soup_othersellers.find_all("article", class_ = "card-b")
    for seller in othersellers:
        offer = seller.find("div", class_ = "-fs20 -b -ltr -tal").text.strip()
        offers.append(offer)
        
    for i in range(0, len(offers)):
                offers[i] = float(''.join(c for c in offers[i] if (c.isdigit() or c =='.')))

    avg_price = "{:.2f}".format(mean(offers))
    
    return avg_price
#%%
def specifications(soup_object):
    column_names = []
    dt = []
    spec_cards = soup_object.find_all("div", class_ = "card-b -fh")
    for card in spec_cards:
        specs = card.find_all("li")
        if specs !=None:
            for spec in specs:
                spec_name = spec.text.strip().split(':')[0]
                spec_name = spec_name.replace(u'\xa0', u'')
                spec_name = spec_name.replace(u'\n', u'')
                spec_name = re.sub('^[·]|^[-]','',spec_name)
                spec_name = spec_name.strip()
                column_names.append(spec_name)
                try:
                    spec_val = spec.text.strip().split(':')[1]
                    spec_val = spec_val.replace(u'\xa0', u'')
                    spec_val = spec_val.replace(u'\n', u'')
                    spec_val = re.sub('^[·]|^[-]','',spec_val)
                    spec_val = spec_val.strip()
                except:
                    spec_val = spec_name                
                dt.append(spec_val)
                
            specs = {column_names[i]: dt[i] for i in range(len(column_names))}
        

    return(specs)

#print(specifications(soup))

#%%
def get_data(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.content, 'lxml')
    try:
        name  = soup.find("h1").text.strip()
    except:
        name = None

    try:
        category = soup.find_all("a", class_ = "cbs")
        unique_category_2 = category[-2].text.strip()
        unique_category = category[-3].text.strip()
    except:
        Unique_category = 'TV'
        unique_category_2 = None

    try:
        make = soup.find_all("div", class_ = "-phs")
        make = make[2]
        make = make.find("div", class_ = "-pvxs")
        make = make.find("a").text.strip()
    except:
        make = None

    try:
        price = soup.find("span", class_ = "-b -ltr -tal -fs24").text.strip()
        price = price.split("-")[0]
        price = float(''.join(c for c in price if (c.isdigit() or c =='.')))
    except:
        price = None
        
    try:
        number_of_offers = soup.find("span", class_ = "-b -prxs").text.strip()
    except:
        number_of_offers = 1

    try:
        avg_price = offers(soup, price)
    except:
        avg_price = price
    try:
        category = category
    except:
        category = "Televisions"
    
    currency = "₦"
    
    countrycode = "NG"

    try:
        specs = specifications(soup)
        print(specs)
    except:
        specs = {}
    
    scrape_link = link
    
    now = datetime.now()
    
    scrape_datetime = now.strftime("%d/%m/%Y %H:%M:%S")

    print(unique_category, unique_category_2)

    tv = {'countrycode':countrycode,
        'category1':unique_category,
        'category2':unique_category_2,
        'tv_title':name,
        'tv_make':make,
        'tv_price':price,
        'numberofoffers':number_of_offers,
        'averageprice':avg_price,
        'currency':currency,
        'tvspecifications': specs,
        'scrapelink': link,
        'scrapedate': scrape_datetime}
    

    
    print(specs)
    return tv


#%%
for link in links:
    data = []
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    mycursor.execute(sql, tv_link)
    time.sleep(1)
    

#%%
df = pd.read_sql('SELECT * FROM data_table', con=engine)
df['tvspecifications'] =df['tvspecifications'].apply(lambda x: dict(eval(x)))
spec_df = df['tvspecifications'].apply(pd.Series)
df_l  = pd.concat([df[['countrycode', 'category1','category2','tv_title', 'tv_make', 'tv_price', 'numberofoffers', 'averageprice', 'currency', 'scrapelink', 'scrapedate']], spec_df.reindex(df.index)], axis=1)
df_long = df_l.set_index(['countrycode', 'category1','category2','tv_title', 'tv_make', 'Model','tv_price', 'numberofoffers', 'averageprice', 'currency', 'scrapelink', 'scrapedate']).stack().reset_index()
df_long.to_sql('jumia_data', engine, if_exists='replace', index=False)
df_long.to_csv("jumia_data_long.csv")
# %%
