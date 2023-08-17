#%%
import time
import logging
import mysql.connector
import pandas as pd
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from statistics import mean
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_url = "https://www.kuantokusta.pt"

def setup_session():
    user_agent = UserAgent().random
    headers = {"User-Agent": user_agent}
    session = requests.Session()
    session.headers.update(headers)
    return session


def establish_db_connection(hostname, dbname, uname, pwd):
    try:
        connection = mysql.connector.connect(
            host=hostname,
            user=uname,
            password=pwd,
            database=dbname,
            autocommit=True
        )
        cursor = connection.cursor()
        logger.info("Database connection established successfully.")
        return connection, cursor
    except Exception as e:
        logger.error("Error establishing database connection: %s", e)
        raise


def create_tv_table(cursor):
    try:
        create_table_query = """
            CREATE TABLE IF NOT EXISTS tv_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                category VARCHAR(255),
                currency VARCHAR(255),
                avg_price FLOAT,
                no_offers INT,
                scrape_link VARCHAR(255),
                scrape_date DATETIME,
                specs JSON,
                tv_details_json JSON
            )
        """
        cursor.execute(create_table_query)
        logger.info("Table 'tv_table' created successfully.")
    except Exception as e:
        logger.error("Error creating 'tv_table': %s", e)
        raise


def get_tv_details(url):
    session = setup_session()

    # Use Selenium to click on the button to get offers
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode (without a visible GUI)

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    try:
        # Click on the "Ver Ofertas" button if it exists
        ver_ofertas_button = driver.find_element(By.CSS_SELECTOR, 'button[data-analytics="product-show-all-stores"]')
        ver_ofertas_button.click()
        time.sleep(5)  # Add a small delay to allow the content to load after clicking

    except:
        pass

    offers_page_parser = BeautifulSoup(driver.page_source, "html.parser")
    breadcrumb = offers_page_parser.find("ul", {"data-ads-id": "breadcrumb"})
    breadcrumb = breadcrumb.find_all("li")[-1].get_text().strip() if breadcrumb else None
    title = offers_page_parser.find("h1").get_text().strip() if offers_page_parser.find("h1") else None
    currency = '€'
    try:
        avg_price = mean(get_offers(offers_page_parser))
    except:
        avg_price = None
    try:
        no_offers = len(get_offers(offers_page_parser))
    except:
        no_offers = 1
    scrape_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    scrape_link = url
    try:
        # Get TV specifications
        specs = get_specs(offers_page_parser)
    except:
        specs = {}
    try:
        # Get TV variations and insert into the database
        variations = get_variations(offers_page_parser)
    except:
        variations = None

    driver.quit()

    tv_details = {
        "title": title,
        "category": breadcrumb,
        "currency":currency,
        "avg_price": avg_price,
        "no_offers": no_offers,
        "scrape_link": scrape_link,
        "scrape_date": scrape_date,
        "specs": specs,
        "variations": variations,
    }

    return tv_details


def get_specs(parser):
    feat_names = []
    feat_vals = []
    features_o = parser.find("div", {"id": "features"})
    features = features_o.find("section", class_="c-gYBZre c-PJLV")
    features = features.find_all("li", class_="c-eHqchX")
    for feature in features:
        feat_names.append(feature.find("span", class_="c-khNXFk").get_text().strip())
        feat_vals.append(feature.find("span", class_="c-gNXYgk").get_text().strip())
    try:
        references = features_o.find_all("div", class_ = "c-gOYXKZ")
        for reference in references:
            feat_names.append(reference.find("span", class_ = "c-cUnbMK").get_text().strip())
            feat_vals.append(reference.find("span", class_="c-ijYvwD").get_text().strip())
    except: pass
    specs = {feat_names[i]: feat_vals[i] for i in range(len(feat_names))}
    return specs


def get_variations(parser):
    is_scraped = 0
    variations = []
    vars = parser.find("div", class_="c-ikzlAw c-ikzlAw-hZNLYh-justScroll-true c-ikzlAw-dkxbN-hasPreview-true")
    vars = vars.find_all("a")
    for var in vars:
        var_link = base_url + var.get("href")
        variations.append(var_link)
    return variations


def get_offers(parser):
    prices = []
    offers = parser.find_all("a", {"data-test-id": "offer-card"})
    for offer in offers:
        offer_price = offer.find("span", {"data-test-id": "offer-price"}).get_text().strip()
        # Remove euro symbol and comma
        offer_price  = offer_price.replace('€', '').replace('.', '').replace(',', '.')
        # Convert the string to a float
        offer_price = float(offer_price )
        prices.append(offer_price)
    print(prices)
    return prices


def insert_tv_details(connection, cursor, tv_details):
    try:
        insert_query = """
            INSERT INTO tv_table (title, category, currency,avg_price, no_offers, scrape_link, scrape_date, specs, tv_details_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            tv_details["title"],
            tv_details["category"],
            tv_details["currency"],
            tv_details["avg_price"],
            tv_details["no_offers"],
            tv_details["scrape_link"],
            tv_details["scrape_date"],
            json.dumps(tv_details["specs"]),
            json.dumps(tv_details)
        ))
        logger.info("TV details inserted successfully.")
    except Exception as e:
        logger.error("Error inserting TV details: %s", e)
        raise


def mark_link_as_scraped(cursor, link):
    try:
        update_query = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = %s"
        cursor.execute(update_query, (link,))
        logger.info(f"Link '{link}' marked as scraped.")
    except Exception as e:
        logger.error(f"Error marking link '{link}' as scraped: {e}")
        raise
if __name__ == "__main__":
    try:
        # Database connection details
        hostname = "localhost"
        dbname = "kuanto_tvs"
        uname = "root"
        pwd = "4156"

        # Establish database connection
        connection, cursor = establish_db_connection(hostname, dbname, uname, pwd)

        # Create 'tv_table' if it doesn't exist
        create_tv_table(cursor)

        df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=connection)
        urls = []
        for i in df_links.tv_link:
            urls.append(i)

        for url in urls:
            tv_details = get_tv_details(url)
            insert_tv_details(connection, cursor, tv_details)
            
            # Mark the current link as scraped
            mark_link_as_scraped(cursor, url)

    except Exception as e:
        logger.error("An error occurred: %s", e)

    finally:
        cursor.close()
        connection.close()


#data cleaning
#%%
kuanto_tvs = mysql.connector.connect(
    host="localhost",  # Replace with your MySQL server hostname
    user="root",  # Replace with your MySQL username
    password="4156",  # Replace with your MySQL password
    database="kuanto_tvs"  ,# Replace with your MySQL database name
    autocommit = True
)


df = pd.read_sql('SELECT * FROM tv_table', con=kuanto_tvs)

# %%
df['specs'] =df['specs'].apply(lambda x: dict(eval(x)))
spec_df = df['specs'].apply(pd.Series)

# %%
spec_df = spec_df[['Referência:', 'Resolução', 'Dimensão do ecrã na diagonal', 'Smart TV', 'Sistema Operativo']]

# %%
df_l  = pd.concat([df[['title', 'no_offers','avg_price', 'currency', 
       'scrape_link', 'scrape_date']], spec_df.reindex(df.index)], axis=1)
df_l = df_l.fillna('Not Found')
df_l = df_l.rename(columns={'Referência:':'Reference','Dimensão do ecrã na diagonal': 'Screen size', 'Resolução': 'Definition', 'Sistema operativo':'Operating system'})
df_l.loc[(df_l['Smart TV'] == 'Not found') & (df_l['title'].str.lower().str.contains('smart')), 'Smart TV'] = 'Sí'
df_l["country_code"] = "PT"
# %%
# %%
df_long = df_l.set_index(["country_code", 'Reference', 'title', 'no_offers', 'avg_price', 'currency', 'scrape_link', 'scrape_date']).stack().reset_index()
df_long.to_csv("kuanto_data_long.csv")
# %%
