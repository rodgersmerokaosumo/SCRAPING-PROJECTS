from datetime import datetime
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selectolax.parser import HTMLParser
import mysql.connector
from fake_useragent import UserAgent

# Generate a random user agent
user_agent = UserAgent().random

falabella_tvs = mysql.connector.connect(
    host="localhost",  # Replace with your MySQL server hostname
    user="root",  # Replace with your MySQL username
    password="4156",  # Replace with your MySQL password
    database="falabella_tvs"  ,# Replace with your MySQL database name
    autocommit = True
)

#%%
mycursor = falabella_tvs.cursor()

df_links = pd.read_sql('SELECT * FROM tv_links WHERE is_scraped = 0', con=falabella_tvs)
tv_links = df_links['tv_link'].tolist()

#%%

# Define the SQL statement to create the "products" table
create_table_query = """
CREATE TABLE IF NOT EXISTS products (
    brand VARCHAR(255),
    title VARCHAR(255),
    avg_price VARCHAR(255),
    currency VARCHAR(255),
    rating VARCHAR(255),
    reviews VARCHAR(255),
    specs TEXT,
    scrape_link VARCHAR(255) UNIQUE,
    scrape_datetime VARCHAR(255)
)
"""
# Execute the create table query
mycursor.execute(create_table_query)

#%%
def scrape_product_data(link):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode (without a visible GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")  # Maximize the browser window
    chrome_options.add_argument("--force-device-scale-factor=0.3")  # Set zoom level to 60%
    chrome_options.add_argument(f"user-agent={user_agent}")
    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)

    # Load the webpage
    driver.get(link)
    time.sleep(3)
    parser = HTMLParser(driver.page_source)

    data = {}

    try:
        brand = parser.css_first("div[class='jsx-1874573512 product-brand fa--brand false']").attrs.get("data-brand")
        data["brand"] = brand
    except:
        data["brand"] = None

    try:
        title = parser.css_first("h1").text()
        data["title"] = title
    except:
        data["title"] = None

    try:
        price_elem = parser.css_first("li[class='jsx-749763969 prices-0']")
        avg_price = price_elem.text().split(" ")[2]
        currency = price_elem.text().split(" ")[0]
        data["avg_price"] = avg_price
        data["currency"] = currency
    except:
        data["avg_price"] = None
        data["currency"] = None

    try:
        rating = parser.css_first("div[itemprop='ratingValue']").text()
        data["rating"] = rating
    except:
        data["rating"] = None

    try:
        reviews = parser.css_first("div[class='bv_numReviews_text']").text()
        data["reviews"] = reviews
    except:
        data["reviews"] = None

    try:
        specs = {}
        spec_table = parser.css_first("table[class='jsx-428502957 specification-table']")
        rows = spec_table.css("tr")
        for row in rows:
            spec_name = row.css_first("td[class='jsx-428502957 property-name']").text()
            spec_val = row.css_first("td[class='jsx-428502957 property-value']").text()
            specs[spec_name] = spec_val
        data["specs"] = specs
    except:
        data["specs"] = {}

    data["scrape_link"] = link
    data["scrape_datetime"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # After you are done, don't forget to close the browser:
    driver.quit()

    return data

def insert_data(data):
    # Prepare the SQL query
    query = "INSERT IGNORE INTO products (brand, title, avg_price, currency, rating, reviews, specs, scrape_link, scrape_datetime) " \
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

    # Convert the dictionary data to a tuple of values in the same order as the query
    values = (
        data["brand"],
        data["title"],
        data["avg_price"],
        data["currency"],
        data["rating"],
        data["reviews"],
        str(data["specs"]),
        data["scrape_link"],
        data["scrape_datetime"]
    )

    # Execute the query with the values
    mycursor.execute(query, values)

    sql = "UPDATE tv_links SET is_scraped = 1 WHERE tv_link = (%s)"
    tv_link = (link,)
    mycursor.execute(sql, tv_link)

    # Commit the changes to the database
    falabella_tvs.commit()
    print(data)




#link = "https://www.falabella.com.co/falabella-co/product/33972788/Televisor-Hyundai-32-Pulgadas-Hd-Smart-Android-By-Google/33972788"
for link in tv_links:
    product_data = scrape_product_data(link)
    insert_data(product_data)

#%%
df = pd.read_sql('SELECT * FROM products', con=falabella_tvs)

# %%
df['reviews'] = df['reviews'].apply(lambda x: x.strip('()'))
df['specs'] =df['specs'].apply(lambda x: dict(eval(x)))
spec_df = df['specs'].apply(pd.Series)
spec_df.head()
# %%
spec_df.columns
# %%
spec_df = spec_df[['Modelo', 'Tamaño de la pantalla', 'Smart TV', 'Resolución', 'Sistema operativo']]
# %%
#%%
df_l  = pd.concat([df[['title', 'brand','avg_price', 'currency', 'rating', 'reviews',
       'scrape_link', 'scrape_datetime']], spec_df.reindex(df.index)], axis=1)
df_l = df_l.fillna('Not Found')

df_l = df_l.rename(columns={'Tamaño de la pantalla': 'Screen size', 'Resolución': 'Definition', 'Sistema operativo':'Operating system'})

#%%
# Update the condition for 'Smart TV'
df_l.loc[(df_l['Smart TV'] == 'Not found') & (df_l['title'].str.lower().str.contains('smart')), 'Smart TV'] = 'Sí'

# Update the conditions for 'Operating system'
mask = (df_l['Operating system'] == 'Not found')
df_l.loc[mask & (df_l['Smart TV'] == 'No'), 'Operating system'] = 'No smart'

mask = (df_l['Operating system'] == 'Not found') & (df_l['Smart TV'] == 'Sí')
df_l.loc[mask & (df_l['brand'].str.lower() == 'samsung'), 'Operating system'] = 'Tizen OS'
df_l.loc[mask & (df_l['brand'].str.lower() == 'lg'), 'Operating system'] = 'WebOS'
# %%
df_long = df_l.set_index(['title', 'brand','Modelo','avg_price', 'currency', 'rating', 'reviews',
       'scrape_link', 'scrape_datetime']).stack().reset_index()
df_long.to_csv("falabella_data_long.csv")
# %%
