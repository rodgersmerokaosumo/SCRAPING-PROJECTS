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
ceneo_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)

mycursor = ceneo_tvs.cursor()

mycursor.execute("use ceneo_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="ceneo_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
driver = webdriver.Chrome(options=options)
#url = "https://www.ceneo.pl/133748377"
base_url = "https://www.ceneo.pl"
is_scraped = 0


#%%
driver.get("https://www.ceneo.pl/133540566")
time.sleep(1)
resp = HTMLParser(driver.page_source)
#%%



# %%
def get_offers(resp):
    prices = []
    offers = resp.css("div[class = 'product-offer__store-with-product']")
    for offer in offers:
        offer_price = offer.css_first("span[class='price']").text().strip().replace(",", ".")
        offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c =='.')))
        prices.append(offer_price)
    return prices


#%%
def get_variants(resp):
    vars = []
    try:
        family = resp.css_first("div[class='product-family__options']")
        fam_links = family.css("a")
        for link in fam_links:
                tv_link = base_url+ link.attrs["href"]
                mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
                vars.append(tv_link)
                print(tv_link)
    except:pass
    return vars

#%%
def get_specs(driver):
    driver.implicitly_wait(2)
    driver.find_element(By.CSS_SELECTOR, "a[title='Informacje o produkcie']").click()
    time.sleep(2)
    resp = HTMLParser(driver.page_source)
    spec_names = []
    spec_vals = []
    specs = resp.css("div[class = 'specs-group']")
    for s in specs:
        spec_h = s.css("th")
        for h in spec_h:
            spec_names.append(h.text().strip().replace("?",""))
    for s in specs:
        spec_d = s.css("td")
        for h in spec_d:
            spec_vals.append(h.text().strip())
    specs = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    return specs

# %%
driver = webdriver.Chrome(options=options)
def get_data(url):
    driver.get(url)
    driver.implicitly_wait(3)
    try:
        cookies = driver.find_element(By.CSS_SELECTOR, "button[data-category='CookiePermission']")
        cookies.click()
    except:pass

    try:
        more = driver.find_element(By.CSS_SELECTOR, "span[class='link link--accent show-remaining-offers__trigger js_remainingTrigger']")
        more.click()
    except:pass

    scheight = .1
    while scheight < 9.9:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .01

    resp = HTMLParser(driver.page_source)

    country_code = "PL"
    try:
        title = resp.css_first("div[class = 'product-top__title'] h1").text().strip()
    except:title = None
    try:
        nb_offers = len(get_offers(resp))
    except: nb_offers = None
    try:
        avg_price = mean(get_offers(resp))
    except: avg_price = None
    try:
        specifications = get_specs(driver)
    except:
        specifications = {}
    currency = "zl"
    category = "Telewizory"
    scraping_date = time.strftime("%Y-%m-%d")
    source_url = url
    variants = get_variants(resp)

    tv = {
        "country_code":country_code,
        "title":title,
        "nb_offers":nb_offers,
        "avg_price":avg_price,
        "avariant":variants,
        "specifications":specifications,
        "currency":currency,
        "category":category,
        "scraping_date":scraping_date,
        "source_url":source_url
    }
    print(len(get_offers(resp)))
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
    mycursor.execute(sql, tv_link)
    time.sleep(1)

df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)

links = []
for i in df_links.tv_link:
    links.append(i)

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
df['specifications'] =df['specifications'].apply(lambda x: dict(eval(x)))
spec_df = df['specifications'].apply(pd.Series)
new=spec_df["Producent"].str.split(">", expand = True)
spec_df["Producent"] = new[0]
df_l  = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df_long = df_l.set_index(["country_code","category","Producent", "Model", "title", "nb_offers", "avg_price","currency", "source_url", "scraping_date"]).stack().reset_index()
# %%
df_long.to_csv("ceneo_tvs.csv")

# %%
