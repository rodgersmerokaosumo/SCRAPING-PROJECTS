#%%
import re
from statistics import mean
import time
import requests
from selectolax.parser import HTMLParser
import mysql.connector
from sqlalchemy import create_engine
import json
import pandas as pd
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import datetime

#%%
# Set the logging level to suppress the error messages
logging.getLogger('selenium').setLevel(logging.ERROR)

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
mycursor.execute("USE tweakers_tvs")

#%%
# Create the tv_data table if it doesn't exist
create_table_query = """
CREATE TABLE IF NOT EXISTS tv_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    link VARCHAR(255) UNIQUE,
    title VARCHAR(255),
    no_offers INT,
    avg_price FLOAT,
    currency VARCHAR(10),
    category VARCHAR(255),
    specifications TEXT,
    date_scraped VARCHAR(10)
)
"""

mycursor.execute(create_table_query)

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine(f"mysql+pymysql://{uname}:{pwd}@{hostname}/{dbname}")

user_agent = UserAgent()

#%%
def smooth_scroll(driver, scroll_height):
    current_height = 0
    while current_height < scroll_height:
        driver.execute_script(f"window.scrollTo(0, {current_height});")
        time.sleep(0.1)
        current_height += 50

#%%

def get_data(link):
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={user_agent.random}")

    # Set up ChromeDriver with the desired options
    driver = webdriver.Chrome(options=options)

    wait = WebDriverWait(driver, 5)

    try:
        headers = {
            'User-Agent': user_agent.random
        }

        payload = {
            'application': 'frontpage',
            'type': 'setpref',
            'action': 'SpecsShowExpanded',
            'output': 'text'
        }

        driver.get(link)
        time.sleep(2)  # Wait for the page to load

        response = requests.post(link, data=payload, headers=headers)

        # Check if the status code is 429 (Too Many Requests)
        if response.status_code == 429:
            # Wait for a certain period of time (e.g., 5 minutes) and then retry the request
            time.sleep(5)  # 300 seconds = 5 minutes
            response = requests.post(link, data=payload, headers=headers)

        status_code = response.status_code
        content = HTMLParser(response.text)

        try:
            category = content.css_first('li[id="tweakbaseBreadcrumbCategory"]').text().strip()
        except:
            category = "TV"

        try:
            title = content.css_first("h1").text().strip()
        except:
            title = None

        def get_alternatives(content):
            is_scraped = 0
            alternatives = content.css_first('div[class="sortable select productEditionSelect"]')
            links = alternatives.css("li")
            for l in links:
                alternative_link = l.css_first("a").attrs["href"]
                mycursor.execute("""INSERT IGNORE INTO tv_links VALUES(%s, %s)""", (alternative_link, is_scraped))
                print(alternative_link)

        def get_prices(content):
            listing = content.css_first("div[id='listing']")
            listing = listing.css("table[class='shop-listing'] tr")
            prices = []
            for l in listing:
                bare_price = l.css_first("td[class='shop-bare-price']").text().strip().replace(",", "").replace(".", ",").replace("-", "")
                prices.append(float(re.sub(r'[^\d.-]', '', bare_price)))

                currency_symbol = re.search(r'([€$£¥])', bare_price).group(1)

            avg_price = mean(prices)
            no_offers = len(prices)
            currency_symbol = currency_symbol
            return avg_price, no_offers, currency_symbol

        try:
            average_price = get_prices(content)[0]
        except:
            average_price = None

        try:
            offers = get_prices(content)[1]
        except:
            offers = None

        try:
            currency = get_prices(content)[2]
        except:
            currency = None

        def get_specs(driver):
            payload = {
                'application': 'frontpage',
                'type': 'setpref',
                'action': 'SpecsShowExpanded',
                'output': 'text'
            }

            driver.get(link)

            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-action="refuseAll"]')))
            ActionChains(driver).move_to_element(cookie_button).click().perform()
            time.sleep(1)

            specs_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li[id="tab_select_specificaties"] a')))
            ActionChains(driver).move_to_element(specs_button).click().perform()
            time.sleep(2)  # Wait for the expanded specs to load

            # Smooth scroll to the bottom of the page
            scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
            smooth_scroll(driver, scroll_height)

            spec_content = HTMLParser(driver.page_source)
            sections = spec_content.css('tbody[class="toggleContent"]')
            spec_name = []
            spec_val = []
            for section in sections:
                rows = section.css("tr")
                for row in rows:
                    spec_name.append(row.css_first("td[class='spec-label']").text())
                    spec_val.append(row.css_first("td[class='spec']").text())
            specs = {spec_name[i]: spec_val[i] for i in range(len(spec_name))}
            return specs

        try:
            specifications = get_specs(driver)
        except:
            specifications = {}

        now = datetime.datetime.now()
        date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")

        tv = {
            "link": link,
            "title": title,
            "no_offers": offers,
            "avg_price": average_price,
            "currency": currency,
            "category": category,
            "specifications": json.dumps(specifications),
            "date_scraped": date_scraped
        }

        insert_query = """
                    INSERT IGNORE INTO tv_data (link, title, no_offers, avg_price, currency, category, specifications, date_scraped)
                    VALUES (%(link)s, %(title)s, %(no_offers)s, %(avg_price)s, %(currency)s, %(category)s, %(specifications)s, %(date_scraped)s)
                    """
        mycursor.execute(insert_query, tv)

        print("Link:", link)
        print("Page Source:")
        print(tv)
        print("-----------")
    finally:
        driver.quit()

def main():
    try:
        df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=engine)
        links = df_links['tv_link'].tolist()

        for link in links:
            try:
                get_data(link)
                sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
                tv_link = (link,)
                mycursor.execute(sql, tv_link)
                time.sleep(1)
            except Exception as e:
                print(f"An error occurred while processing link: {link}")
                print(f"Error message: {str(e)}")
            time.sleep(2)
    except Exception as e:
        print(f"An error occurred while retrieving links from the database.")
        print(f"Error message: {str(e)}")

main()

#%%
# Clean and process the scraped data
df = pd.read_sql('SELECT * FROM tv_data', con=engine)
df['specifications'] = df['specifications'].apply(lambda x: dict(eval(x)))
spec_df = df['specifications'].apply(pd.Series)
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df.drop(["specifications"], axis=1, inplace=True)

#%%
df.columns.to_list()
# %%
df_long = df.set_index(['Introductiejaar', 'Merk', 'SKU', 'link', 'title', 'no_offers', 'avg_price','currency', 'category', 'date_scraped']).stack().reset_index()

df_long.to_sql('processed_data_table', engine, if_exists='replace', index=False)
df_long.to_csv('processed_data.csv', index=False)