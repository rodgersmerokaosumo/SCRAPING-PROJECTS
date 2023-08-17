#%%
import time
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selectolax.parser import HTMLParser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine
from fake_useragent import UserAgent

user_agent = UserAgent().random
# Configure Chrome options
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Run Chrome in headless mode (without a visible GUI)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--start-maximized")  # Maximize the browser window
chrome_options.add_argument("--force-device-scale-factor=0.4")  # Set zoom level to 60%
chrome_options.add_argument(f"user-agent={user_agent}")
# Create a new instance of the Chrome driver
driver = webdriver.Chrome(options=chrome_options)

#%%
# Database connection details
hostname = "localhost"
dbname = "falabella_tvs"
uname = "root"
pwd = "4156"

# Establish database connection
falabella_tvs = mysql.connector.connect(
    host=hostname,
    user=uname,
    password=pwd,
    autocommit=True
)
mycursor = falabella_tvs.cursor()
mycursor.execute("DROP DATABASE IF EXISTS falabella_tvs")
mycursor.execute("CREATE DATABASE IF NOT EXISTS falabella_tvs")
mycursor.execute("USE falabella_tvs")
mycursor.execute("""CREATE TABLE IF NOT EXISTS tv_links (tv_link VARCHAR(200) UNIQUE, is_Scraped TINYINT)""")

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine(f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}")

#%%
# Load the webpage
is_scraped = 0
page = 1
def get_links(driver):
    # Create a Selectolax parser object to parse the HTML
    parser = HTMLParser(driver.page_source)
    # Use Selectolax methods to extract data from the parsed HTML
    product_titles = parser.css('div[class = "jsx-200723616 search-results-list"]')
    for title in product_titles:
        pod = title.css_first("div[data-pod = 'catalyst-pod']")
        tv_link  = pod.css_first("a").attrs["href"]
        mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (tv_link, is_scraped))
        print(tv_link)
    time.sleep(3)
    #%%
  
#%%
for i in range(1,10):
    driver.get(f"https://www.falabella.com.co/falabella-co/category/cat5420971/Smart-TV?f.product.L2_category_paths=cat50868%7C%7CTecnolog%C3%ADa%2Fcat1360967%7C%7CTV+y+Video%2Fcat5420971%7C%7CSmart+TV&page={i}")
    get_links(driver)

#%%
# After you are done, don't forget to close the browser:
driver.quit()

#%%
