#%%
from statistics import mean
import requests
from bs4 import BeautifulSoup
import pandas as pd
import mysql.connector
from datetime import datetime
#%%
belgium_tvs = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
charset = 'utf8'
)

mycursor = belgium_tvs.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS belgium_tvs")

#%%
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="belgium_tvs"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%
mycursor.execute("use belgium_tvs")

#%%
baseurl = "https://www.123comparer.be"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}

#%%
url = "https://www.123comparer.be/Televiseur/17782964.html"

#%%
def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res
#%%
def get_offers(soup):
    offer_list = []
    offers = soup.find("div", {"id":"myTableClass"})
    offers = offers.find_all("p", class_ = "myTr myTrProd")
    for offer in offers:
        try:
            offer_price = offer.find("span", {"class":"myTd center prix myTd7"})
            offer_price = offer_price.text.strip().split("€")[0].replace(",", ".")
            offer_price = float(''.join(c for c in offer_price if (c.isdigit() or c == '.')))
        except:
            offer_price = None
        offer_list.append(offer_price)
    try:
        avg_price  = mean(offer_list)
    except:
        avg_price = None
    try:
        no_offers =  len(offer_list)
    except:
        no_offers = 0

    return avg_price, no_offers

#%%

def get_specs(soup):
    spec_name = []
    spec_val = []
    table = soup.find("table", class_ = "tableauCarac")
    rows = table.find_all("tr")
    for dat in rows:
        spec_data = dat.find_all("td")
        try:
            spec_d = spec_data[0].text
        except:
            spec_d = None
        spec_name.append(spec_d)
        try:
            spec_v = spec_data[1].text
        except:
            spec_v = None
        spec_val.append(spec_v)
    specs = {spec_name[i]: spec_val[i] for i in range(len(spec_name))}
    return specs


def get_specs2(soup):
    spc_names = []
    spc_vals = []
    spcs = soup.find("ul", class_ = "blocCarac")
    spcs = spcs.find_all("li")
    for spc in spcs:
        try:
            spc_name = spc.text.strip().split(":")[0].replace(" ", "")
        except:
            spc_name = None
        try:
            spc_val = spc.text.strip().split(":")[1]
        except:
            spc_val = None
        spc_names.append(spc_name)
        spc_vals.append(spc_val)
    spcs_ = {spc_names[i]: spc_vals[i] for i in range(len(spc_names))}
    return spcs_


#%%
k = requests.get(url).text
soup=BeautifulSoup(k,'html.parser')
get_specs(soup)
#%%

def get_data(url):
    k = requests.get(url).text
    soup=BeautifulSoup(k,'html.parser')
    try:
        title = soup.find("h1").text.strip()
    except:
        title = None
    try:
        links = soup.find("div", {"id":"filAriane2"})
        category = links.find_all("li", {"itemprop":"itemListElement"})[-1].text.strip()
    except:
        category = None
    try:
        average_prices, no_offers = get_offers(soup)
    except:
        average_prices = None
        no_offers = None
    try:
        specifications = get_specs(soup)
    except:
        specifications = {}

    try:
        spec_sum = get_specs2(soup)
    except:
        spec_sum = {}
    country = "BE"
    currency = "€"
    scrape_link = url

    now = datetime.now()

    scrape_datetime = now.strftime("%d/%m/%Y %H:%M:%S")

    tv = {
        "currency": currency,
        "countrycode": country,
        "title":title,
        "category":category,
        "specifications":specifications,
        "spec_summary":spec_sum,
        "avg price": average_prices,
        "offers":no_offers,
        "scrapelink": scrape_link,
        "scrapedate": scrape_datetime,
    }

    return tv

#%%
df_links = pd.read_sql('SELECT * FROM tv_links WHERE NOT tv_link LIKE "%%voir%%" and is_scraped = 0;', con=engine)

#%%
tv_links = []
for i in df_links['tv_link']:
    tv_links.append(i)

#%%
for link in tv_links:
    data = []
    print(link)
    data.append(get_data(link))
    df = pd.DataFrame.from_dict(data)
    df = df.astype(str)
    df.to_sql('data_table', con=engine, if_exists="append", index=False)
    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    link = (link,)
    mycursor.execute(sql, link)
    belgium_tvs.commit()
#%%
df = pd.read_sql('SELECT * FROM data_table', con=belgium_tvs)
df['specifications'] =df['specifications'].apply(lambda x: dict(eval(x)))
df['spec_summary'] =df['spec_summary'].apply(lambda x: dict(eval(x)))
spec_df = df['specifications'].apply(pd.Series)
spec_sum_df = df['spec_summary'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df = pd.concat([df, spec_sum_df.reindex(df.index)], axis=1)
df.drop(['specifications', 'spec_summary'], axis = 1,  inplace=True)
#%%
#%%
df_long = df.set_index(['countrycode', 'category','title', 'Marque', 'offers', 'avg price', 'currency', 'scrapelink', 'scrapedate']).stack().reset_index()
df_long

#%%
df.to_csv("data_wide.csv")
df_long.to_csv("data_long.csv")
#df.to_sql('details', engine, if_exists='append', index=False)





