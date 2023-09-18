#%%
from statistics import mean
import time
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selectolax.parser import HTMLParser
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
toppreise_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)

mycursor = toppreise_tvs.cursor()

mycursor.execute("use toppreise_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="toppreise_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
driver = webdriver.Chrome()
url = "https://www.toppreise.ch/preisvergleich/TV-Geraete/SAMSUNG-QE65S95BATXXN-OLED-S95B-2022-p688730?selsort=rd"
base_url = "https://www.toppreise.ch"
is_scraped = 0

#%%



#%%
def get_prices(resp):
    offers = []
    prices = resp.css("div.Plugin_Offer.f_clickable.col-12.active.productDetailsOfferList div.Plugin_Price")
    for price in prices:
        offer_price = price.text().replace("'", "").strip()
        offer_price = float(offer_price)
        offers.append(offer_price)
    no_offers = len(offers)
    avg_price = round(mean(offers), 2)
    return no_offers, avg_price




def get_path(resp):
    path = []
    menus = resp.css("span.f_hasBreadCrumbMenu")
    for menu in menus:
        path.append(menu.text())
    path = '/'.join(path)
    return path
# %%
def get_first_specs(soup):
    spec_names = []
    spec_vals = []
    content = soup.find("div", class_ = "Plugin_ProductNgf row tabbedContainer pt-5")
    content = content.find("div", class_ = "col-12 my-3")
    properties  = content.find_all("div", class_ = "col-12 mt-2")
    for property in properties:
        spec_name = property.find("div", class_="col-auto").text.strip()
        spec_value = property.find(class_="col-12 col-md").text.strip()
        spec_names.append(spec_name)
        spec_vals.append(spec_value)
    specs_f = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    return specs_f


# %%
def get_specs(soup):
    spec_names = []
    spec_vals = []
    content = soup.find("div", class_ = "Plugin_ProductNgf row tabbedContainer pt-5")
    properties  = content.find_all("div", class_ = "Plugin_ProductNgfFeatureCategory opened")
    for property in properties:
        content = property.find_all("div", class_ = "Plugin_ProductNgfFeature")
        for feature in content:
            spec_name = feature.find("div", class_="name").text.strip()
            spec_value = feature.find(class_="value").text.strip()
            spec_names.append(spec_name)
            spec_vals.append(spec_value)
    specs_f = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    spec_a = get_first_specs(soup)
    spec_a.update(specs_f)
    return spec_a



#%%
def get_data(url):
    driver.get(url)
    driver.implicitly_wait(1)
    try:
        button = driver.find_element(By.CLASS_NAME, "f_submit.btnInverted")
        button.click()
    except: pass
    scheight = .1
    while scheight < 9.9:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .008
    time.sleep(2)

    resp = HTMLParser(driver.page_source)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    try:
        currency = resp.css_first("div.currency").text()
    except:
        currency = None
    try:
        title  = resp.css_first("h1").text()
    except:
        title = None
    try:
        path = get_path(resp)
    except:
        path = None
        
    try:
        specs = get_specs(soup)
    except:
        specs = None
    try:
        offers = get_prices(resp)[0]
        avg_price  = get_prices(resp)[1]
    except:
        offers = None
        avg_price = None

    now = datetime.datetime.now()
    date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")

    tv = {
        "path": path,
        "currency":currency,
        "title":title,
        "specifications":specs,
        "offers":offers,
        "avg_price":avg_price,
        "scrape_link":url,
        "date_scraped":date_scraped
    }
    #print(tv)
    return tv

# %%
#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=toppreise_tvs)
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
        df.to_sql('data_table', engine, if_exists='append', index=False, schema='toppreise_tvs')
        sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
        tv_link = (link,)
        mycursor.execute(sql, tv_link)
        toppreise_tvs.commit()
        count = count + 1
        print(count)
# %%
def set_smart_tv(row):
    if row['Operating system'] != 'Not found':
        return 'Yes'
    else:
        return 'Not Found'
    

df = pd.read_sql("SELECT * FROM data_table", con=toppreise_tvs)
df["specifications"] = df["specifications"].apply(lambda x : dict(eval(x)))
df2 = df["specifications"].apply(pd.Series)
df = pd.concat([df, df2], axis=1).drop('specifications', axis=1).astype(str)
df= df.fillna('Not Found')
df.columns
# %%
# Rename columns using the rename() method
df.rename(columns={'HD-Spezifikation': 'Definition', 'Bilddiagonale': 'Screen size', 'Betriebssystem':'Operating system', 'Marke':"brand"}, inplace=True)
df["Digital tuner standard"] = "DVB"
df['Smart TV'] = df.apply(set_smart_tv, axis=1)
df["country"] = "CH"

#%%
df_long = df.set_index(['country', 'brand', 'Herstellerartikelnummer:', 'title', 'offers', 'avg_price', 'currency', 'path',
       'scrape_link', 'date_scraped']).stack().reset_index()
df_long.to_csv("toppreise.csv",)

#%%
