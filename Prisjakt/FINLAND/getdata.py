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
options.add_argument('-headless')

#%%

driver = webdriver.Chrome(options=options)


#%%
##create database
prisjakt_finland_tvs= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

mycursor = prisjakt_finland_tvs.cursor()

mycursor.execute("use prisjakt_finland_tvs")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="prisjakt_finland_tvs"
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

# %%
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
    specs = []
    spec_names = []
    spec_vals = []
    properties  = resp.css_first("div[id = '#properties']")
    items = properties.css("div[role = 'listitem']")
    for item in items:
        item_title = item.css_first("span[class = 'Text--d6brv6 YbaBe bodysmalltext PropertyName-sc-1jnk5ag-5 hEdIXF']").text()
        spec_names.append(item_title)
        item_value = item.css_first("span[class = 'Text--d6brv6 fSxdjg bodysmalltext PropertyValue-sc-1jnk5ag-6 etcKHO']").text()
        spec_vals.append(item_value)
    specs = {spec_names[i]: spec_vals[i] for i in range(len(spec_names))}
    return specs
# %%
print()

#%%

def get_data(url):
    driver.get(url)
    driver.implicitly_wait(2.5)
    scheight = .1
    while scheight < 9.9:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/%s);" % scheight)
        scheight += .008
    try:
        cookies = driver.find_element(By.CSS_SELECTOR, 'button.AcceptButtonCookieBanner.ButtonCookieBanner')
        cookies.click()
    except: pass
    try:
        buttons = driver.find_element(By.CSS_SELECTOR, 'button.BaseButton--z97mxu.gxAgcF.textbutton')
        for button in buttons:
            button.click()
    except: pass
    
    resp = HTMLParser(driver.page_source)

    country = "FI"

    currency = "€"

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

    try:
        specs = get_specs(resp)
    except: specs = {}

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



#%%
#%%
for link in tv_links:
    data = []
    print(link)
    data.append(get_data(link+"#properties"))
    df = pd.DataFrame.from_dict(data).astype(str)
    df.to_sql('data_table', engine, if_exists='append', index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    engine.execute(sql, tv_link)
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
df_long = df.set_index(['country', 'category','title', 'Valmistaja', 'avg_price', 'offers', 'currency', 'scrape_link', 'date_scraped']).stack().reset_index()
df_long.to_sql('cleaned_data', engine, if_exists='replace', index=False)
df_long.to_csv('sample.csv')
# %%
