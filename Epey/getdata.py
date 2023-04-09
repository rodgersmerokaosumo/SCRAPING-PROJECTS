#%%
from statistics import mean
import time
import requests
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
from datetime import datetime
import mysql.connector
import pandas as pd

ua = UserAgent()
print(ua.random)
header = {'User-Agent':str(ua.random)}

link = "https://www.epey.com/televizyon/philips-77oled937.html"


#%%
epey_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = epey_tvs.cursor()
#mycursor.execute("CREATE DATABASE IF NOT EXISTS epey_tvs")

#%%
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="epey_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use epey_tvs")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(500) UNIQUE, is_scraped TINYINT)""")

#%%
def get_offers(resp):
    prices = []
    offers = resp.css("span.urun_fiyat")
    for offer in offers:
        offer_price = offer.text().strip().split(" ")[0].replace(".", "").replace(",", ".")
        offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c =='.')))
        prices.append(offer_price)
    return prices
# %%
def get_specs(resp):
    spec_names = []
    spec_vals = []
    specs_list = []
    specs = resp.css("ul.grup")
    for spec in specs:
        specs_list.append(spec.css("li"))

    specs = [item for sublist in specs_list for item in sublist]
    for spec in specs:
        spec_names.append(spec.css_first("li strong").text().strip())
        spec_vals.append(spec.css_first("li span").text().strip())
    specifications = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    return specifications
#return specifications
# %%
def get_variants(resp):
    is_scraped = 0
    variants = resp.css("div[id = 'varyant'] a")
    len(variants)
    for variant in variants:
        tv_link = variant.attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        epey_tvs.commit()
    
    return len(variants)

# %%

def get_data(link):
    payload = {"cerez": "MTkzMjEr", }
    response = requests.post(link, headers=header, data=payload, verify=False)
    print(response.status_code)
    resp = HTMLParser(response.text)
    try:
        title = resp.css_first("h1").text().strip()
    except: title = None
    try:
        crumbs = resp.css("div[class = 'yol'] a")
        category = crumbs[-2].text().strip()
    except:
        category = "TV"
    try:
        crumbs = resp.css("div[class = 'yol'] a")
        brand = crumbs[-1].text().strip()
    except:brand =None
    try:
        reference = resp.css_first("span.kod").text().strip()
    except: reference = None

    try:
        no_offers = len(get_offers(resp))
    except: no_offers = 1

    try:
        avg_price = mean(get_offers(resp))
    except:
        avg_price = 0

    try:
        specifications = get_specs(resp)
    except:specifications = {}

    country = "TR"

    scrape_link = link
    
    now = datetime.now()

    currency = "TL"
    
    scrape_datetime = now.strftime("%d/%m/%Y %H:%M:%S")

    try:
        get_variants(resp)
    except:pass

    tv = {
        "country":country,
        "category":category,
        "brand":brand,
        "title":title,
        "reference":reference,
        "no_offers":no_offers,
        "avg_price":avg_price,
        "currency":currency,
        "specifications":specifications,
        "scrape_link":scrape_link,
        "scrape_time":scrape_datetime
    }

    return tv


#%%

df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)

links = []
for i in df_links.tv_link:
    links.append(i)

#%%
for link in links:
    data = []
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    engine.execute(sql, link)
    time.sleep(1)
# %%

df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)

links = []
for i in df_links.tv_link:
    links.append(i)

#%%
for link in links:
    data = []
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    engine.execute(sql, link)
    time.sleep(1)


#%%
df = pd.read_sql('SELECT * FROM data_table', con=engine)
df['specifications'] =df['specifications'].apply(lambda x: dict(eval(x)))
spec_df = df['specifications'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df.drop(['specifications'], axis = 1,  inplace=True)
# %%
df_long = df.set_index(['country', 'category','brand', 'title', 'reference', 'no_offers', 'avg_price', 'currency','Çıkış Yılı','scrape_time', 'scrape_link']).stack().reset_index()
#%%
df_long.to_csv("tv_data_long.CSV")
df.to_csv('tv_data.csv')
# %%
