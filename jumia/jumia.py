#%%
from locale import currency
from requests_html import HTMLSession
import requests
from bs4 import BeautifulSoup
import pandas as pd
import httplib2
import re
from parsel import Selector
from statistics import mean
import time
from datetime import datetime
headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
http = httplib2.Http()
import mysql.connector

#%%
headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

base_url = "https://www.jumia.com.tn"
url = 'https://www.jumia.com.tn/catalog/?q=televisions'

#%%
##create database
justwatch_tv_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = justwatch_tv_db.cursor()

mycursor.execute("CREATE DATABASE IF NOT EXISTS jumia_tvs")

#%%
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="jumia_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
productlinks = []
for x in range(1,26):
    r = requests.get(f"https://www.jumia.com.tn/catalog/?q=televisions&page={x}#catalog-listing")
    soup = BeautifulSoup(r.content, 'lxml')
    productlist = soup.find('div', class_ = '-paxs row _no-g _4cl-3cm-shs')
    productlist = productlist.find_all('article', class_ = 'prd _fb col c-prd')

    for product in productlist:
        prod_link = product.find("a", class_ = "core")
        productlinks.append(base_url+prod_link['href'])
        #print((base_url+prod_link['href']))

#%%
df_tv_links = pd.DataFrame(productlinks, columns = ['Tv Links'])
# Convert dataframe to sql table                                   
df_tv_links.to_sql('title_links', engine, if_exists='replace', index=False)

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
                column_names.append(spec_name)
                try:
                    spec_val = spec.text.strip().split(':')[1]
                except:
                    spec_val = spec_name                
                dt.append(spec_val)
                
            specs = {column_names[i]: dt[i] for i in range(len(column_names))}
        

    return(specs)

#print(specifications(soup))

#%%

testlink = "https://www.jumia.com.tn/tv-50-led-hdr-ua50au7000xmv-garantie-2ans-samsung-mpg26341.html"
def get_data(link):
    r = requests.get(link)
    soup = BeautifulSoup(r.content, 'lxml')
    name  = soup.find("h1", class_ = "-fs20 -pts -pbxs").text.strip()
    try:
        make = soup.find_all("div", class_ = "-phs")
        make = make[2]
        make = make.find("div", class_ = "-pvxs")
        make = make.find("a").text.strip()
    except:
        make = None

    try:
        price = soup.find("span", class_ = "-b -ltr -tal -fs24").text.strip()
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
    
    currency = "TND"
    
    countrycode = "TN"

    specs = specifications(soup)
    
    scrape_link = link
    
    now = datetime.now()
    
    scrape_datetime = now.strftime("%d/%m/%Y %H:%M:%S")

    tv = {'countrycode':countrycode,
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
data = []
for link in productlinks:
    data.append(get_data(link))
    
    
#%%
df = pd.DataFrame.from_dict(data)
spec_df = df['tvspecifications'].apply(pd.Series)
df_l  = pd.concat([df[['countrycode', 'tv_title', 'tv_make', 'tv_price', 'numberofoffers', 'averageprice', 'currency', 'scrapelink', 'scrapedate']], spec_df.reindex(df.index)], axis=1)
df_long = df_l.set_index(['countrycode', 'tv_title', 'tv_make', 'tv_price', 'numberofoffers', 'averageprice', 'currency', 'scrapelink', 'scrapedate']).stack().reset_index()
df_long
# %%

df_long.to_sql('jumia_data', engine, if_exists='replace', index=False)
# %%

df.to_csv("jumia_data_wide.csv")
df_long.to_csv("jumia_data_long.csv")
# %%
