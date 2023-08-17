import time
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
from selenium.common.exceptions import NoSuchElementException

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")

# Database connection details
hostname = "localhost"
dbname = "tweakers_tvs"
uname = "root"
pwd = "4156"

# Establish database connection
tweakers_tvs = mysql.connector.connect(
    host=hostname,
    user=uname,
    password=pwd,
    autocommit=True
)
mycursor = tweakers_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS tweakers_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS tweakers_tvs")
mycursor.execute("USE tweakers_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links (tv_link VARCHAR(200) UNIQUE, is_Scraped TINYINT)""")

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine(f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}")

# Initialize Chrome webdriver
#service = Service('path/to/chromedriver')  # Replace with the path to your chromedriver executable
driver = webdriver.Chrome(options=chrome_options)

def get_links(driver, link):
    is_scraped = 0
    try:
        driver.get(link)
        time.sleep(3)  # Wait for the page to load
        products = driver.find_elements(By.CSS_SELECTOR, "tr.largethumb")
        for product in products:
            tv_link = product.find_element(By.CSS_SELECTOR, "a.editionName").get_attribute("href")
            mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
            print(tv_link)
        next_page_link = driver.find_element(By.CSS_SELECTOR, "a.ctaButton.secondary.next").get_attribute("href")
        return next_page_link
    except NoSuchElementException:
        print("No more pages to scrape.")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

try:
    initial_page = "https://tweakers.net/televisies/vergelijken/"
    current_page = initial_page

    while current_page:
        print(f"Scraping page: {current_page}")
        current_page = get_links(driver, current_page)

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    driver.quit()
    tweakers_tvs.close()
