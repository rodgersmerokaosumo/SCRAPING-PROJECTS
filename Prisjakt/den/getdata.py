#%%
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from statistics import mean
import time
import pandas as pd
from selectolax.parser import HTMLParser
import datetime
import mysql.connector
from sqlalchemy import create_engine

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1200")
#options.add_argument('-headless')

#%%
##create database
prisjakt_denmark_tvs= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)

mycursor = prisjakt_denmark_tvs.cursor()

mycursor.execute("use prisjakt_denmark_tvs")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="prisjakt_denmark_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)
tv_links = []
for i in df_links['tv_link']:
    tv_links.append(i)

#%%
#%%
def get_offers(resp):
    offers = []
    prices = resp.css("*[data-test = 'PriceLabel']")
    for price in prices:
        offer_price = price.text().strip()
        offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c =='.')))
        offers.append(offer_price)
    return offers

#%%
def get_specs(resp):
    specs = resp.css("div[role = 'listitem']")
    spec_name = []
    spec_val = []
    for spec in specs:
        try:
            spec_name.append(spec.css_first("span[class = 'Text--1ka53sf dsObrg bodysmalltext PropertyName-sc-0-5 lolJzQ']").text())
        except: pass
        try:
            spec_val.append(spec.css_first("span[class = 'Text--1ka53sf jytHci bodysmalltext PropertyValue-sc-0-6 guNUSr']").text())
        except: pass
    specs = {spec_name[i]: spec_val[i] for i in range(len(spec_name))}
    print(specs)
    return specs

#%%
driver = webdriver.Chrome(options=options)

#%%
def get_data(url):
    driver.get(url+'#properties')
    time.sleep(2)
    try:
        cookies = driver.find_element(By.CSS_SELECTOR, 'button.AcceptButtonCookieBanner.ButtonCookieBanner')
        cookies.click()
    except: pass
    try:
        buttons = driver.find_element(By.CSS_SELECTOR, 'button.BaseButton--z97mxu.gxAgcF.textbutton')
        for button in buttons:
            button.click()
    except: pass
    

    country = "DEK"

    currency = "KR"

    try:
        category = resp.css_first("span[data-test = 'Crumb']").text()
    except: category = "TV"

    try:
        title = title = resp.css_first("h1").text()
    except: title = None
    try: 
        rating = resp.css_first("span.RateNumber-sc-14ktvqu-6.kfKsvH").text()
    except:rating = None
    try:
        reviews = resp.css_first("span.Counter-sc-14ktvqu-1.kfbfVX").text()
    except: reviews = None

    specs = get_specs(resp)

    try: 
        avg_price = mean(get_offers(resp))
    except: avg_price = None

    try: 
        offers = len(get_offers(resp))
    except: offers = None

    scrape_link = url

    now = datetime.datetime.now()
    date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")

    print(specs)

    tv = {
        "category":category,
        "country":country,
        "currency":currency,
        "title":title,
        "rating":rating,
        "reviews":reviews,
        "specs":specs,
        "avg_price":avg_price,
        "offers":offers,
        "scrape_link":scrape_link,
        "date_scraped":date_scraped
    }

    return tv

# %%
for link in tv_links:
    data = []
    print(link)
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data).astype(str)
    df.to_sql('data_table', engine, if_exists='append', index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    mycursor.execute(sql, tv_link)
    time.sleep(3)

#%%
df_links = pd.read_sql('SELECT * FROM data_table WHERE specs = "{}"', con=engine)
empty_links = []
for i in df_links['scrape_link']:
    empty_links.append(i)

for link in empty_links:
    data = []
    print(link)
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data).astype(str)
    df.to_sql('data_table', engine, if_exists='append', index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    mycursor.execute(sql, tv_link)
    time.sleep(3)

#%%
import pandas as pd
df = pd.read_sql('SELECT * FROM data_table', con=engine)
#df = df.fillna("NOT AVAILABLE")
df['specs'] =df['specs'].apply(lambda x: dict(eval(x)))
spec_df = df['specs'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df.drop(["specs"], axis = 1,  inplace=True)

#%%
df_long = df.set_index(['country', 'category','title', 'Mærke', 'avg_price', 'offers', 'currency', 'scrape_link', 'date_scraped']).stack().reset_index()
df_long.to_sql('cleaned_data', engine, if_exists='replace', index=False)
df_long.to_csv('sample.csv')

# %%