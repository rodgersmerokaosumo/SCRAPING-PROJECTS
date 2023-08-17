from bs4 import BeautifulSoup
import mysql.connector
import pymysql
from sqlalchemy import create_engine
from fake_useragent import UserAgent
import requests

# Set headers with a random user agent
headers = {"User-Agent": UserAgent().random}

# Create a MySQL database connection
kuanto_tvs = mysql.connector.connect(
    host="localhost",
    user="root",
    password="4156",
    autocommit=True
)

mycursor = kuanto_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS kuanto_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS kuanto_tvs")
mycursor.execute("USE kuanto_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links(tv_link varchar(200) UNIQUE, is_scraped TINYINT)""")

# Credentials for database connection
hostname = "localhost"
dbname = "kuanto_tvs"
uname = "root"
pwd = "4156"

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine(f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}")

base_url = "https://www.kuantokusta.pt"
link = "https://www.kuantokusta.pt/c/271/televisores-tv-led-lcd"

def get_links(link):
    response = requests.get(link, headers=headers)
    if response.status_code == 200:
        parser = BeautifulSoup(response.content, "html.parser")
        product_titles = parser.select('div.product-item-inner')

        for title in product_titles:
            tv_link = base_url + title.select_one('a')['href']
            is_scraped = 0  # Set as needed
            mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
    
        next_page_element = parser.select_one('ul.pagination li:last-child a')
        next_page = base_url + next_page_element['href'] if next_page_element else None
        
        if next_page == link:
            next_page = None
        
        print(next_page)

        return next_page

while link:
    link = get_links(link)

# Close the database connection
kuanto_tvs.close()
