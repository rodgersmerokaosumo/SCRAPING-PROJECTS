#%%
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import mysql.connector as mysql
import mysql.connector
from sqlalchemy import create_engine
ua = UserAgent()
headers = {'User-Agent':str(ua.random)}

#headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

#%%
##create database
argentina_mercado_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
    auth_plugin = 'mysql_native_password'
)

mycursor = argentina_mercado_db.cursor()

mycursor.execute("DROP DATABASE  IF EXISTS argentina_mercado_db")
mycursor.execute("CREATE DATABASE  IF NOT EXISTS argentina_mercado_db")
mycursor.execute("use argentina_mercado_db")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials to database connection
hostname="localhost"
dbname="argentina_mercado_db"
uname="root"
pwd="4156"

#%%
# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))


#%%
url = "https://listado.mercadolibre.com.ar/tv#D[A:Tv]"
pages = []
pages.append(url)
for i in range(43):
  try:
        i = requests.get(url, headers=headers).text
        soup=BeautifulSoup(i,'html.parser')
        link = soup.find("ul", {"role":"navigation"})
        link = link.find("li", class_ = "andes-pagination__button andes-pagination__button--next shops__pagination-button")
        try:
          i = link.find("a", class_ = "andes-pagination__link shops__pagination-link ui-search-link").get('href')
          url = i
          pages.append(i)
          print(f'pages scraped {len(pages)}')
        except:
            pass
  except:
        i = requests.get(url, headers=headers).text
        soup=BeautifulSoup(i,'html.parser')
        link = soup.find("ul", {"role":"navigation"})
        link = link.find("li", class_ = "andes-pagination__button andes-pagination__button--next shops__pagination-button")
        try:
          i = link.find("a", class_ = "andes-pagination__link shops__pagination-link ui-search-link").get('href')
          url = i
          pages.append(i)
          print(f'pages scraped {len(pages)}')
        except:
            pass
  else:
      pass
#%%
pages
#%%
links = []
is_scraped =0
for page in pages:
    k = requests.get(page, headers=headers).text
    soup = BeautifulSoup(k, 'html.parser')
    items = soup.find_all("li", class_ = "ui-search-layout__item shops__layout-item")
    for item in items:
        link = item.find("a", class_ = "ui-search-item__group__element shops__items-group-details ui-search-link").get("href")
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (link, is_scraped))
        argentina_mercado_db.commit()
        links.append(link)
        print(f"{link} : is scraped.")
#%%
print(len(links))

#%%

# %%
