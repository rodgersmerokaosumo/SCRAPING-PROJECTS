#%%
import datetime
import pandas as pd
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selectolax.parser import HTMLParser
import time
from sqlalchemy import create_engine


#%%
##create database
tvguide_db= mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156",
  autocommit = True
)

mycursor = tvguide_db.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS tvguide_db")
mycursor.execute("use tvguide_db")
#mycursor.execute("""CREATE TABLE IF NOT EXISTS tvs(title varchar(200), rating varchar(50), offers varchar(100), specs VARCHAR(500));""")

# Credentials to database connection
hostname="localhost"
dbname="tvguide_db"
uname="root"
pwd="4156"


# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

#%%

# Create the table if it doesn't exist
create_table = """
CREATE TABLE IF NOT EXISTS data_table (
    channel VARCHAR(255),
    start_time VARCHAR(255),
    end_time VARCHAR(255),
    day VARCHAR(255),
    program VARCHAR(255),
    description TEXT,
    subgenre VARCHAR(255),
    genre VARCHAR(255),
    live VARCHAR(255),
    date_scraped VARCHAR(255)
)
"""
mycursor.execute(create_table)



#%%
options = webdriver.ChromeOptions()
options.add_argument('--ignore-ssl-errors=yes')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--headless')  # Run Chrome in headless mode
driver = webdriver.Chrome(options=options)

driver.maximize_window()
# Zoom out the page by executing a JavaScript command
driver.execute_script("document.body.style.zoom = '60%'")  # Adjust the zoom level as per your requirement

driver.get("https://www.tvtoday.de/tv-programm/sport/")
driver.delete_all_cookies()

#%%
# Check if the iframe with title "SP Consent Message" exists
iframe_present = EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[title="SP Consent Message"]'))

time.sleep(2)
if iframe_present(driver):
    # Switch to the iframe
    iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[title="SP Consent Message"]')
    driver.switch_to.frame(iframe)

    # Find and click the button with title "Akzeptieren"
    accept_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Akzeptieren"]')))
    accept_button.click()

    # Switch back to the default content
    driver.switch_to.default_content()

# Find the <a> tag with href="/tv-programm/sport/?date=twoweeks"
link_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/tv-programm/sport/?date=twoweeks"]')))
# Click on the link
link_element.click()

time.sleep(2)
# Set up scrolling parameters
step_scroll = 500  # The scrolling distance for each iteration
scroll_pause_time = 3  # Time to pause between scrolling

# Get initial scroll position
scroll_pos_init = driver.execute_script("return window.pageYOffset;")

while True:
    time.sleep(3)
    # Scroll down by the specified distance
    driver.execute_script(f"window.scrollBy(0, {step_scroll});")
    
    # Wait for the page to load the content
    time.sleep(scroll_pause_time)
    
    # Get the updated scroll position
    scroll_pos_end = driver.execute_script("return window.pageYOffset;")
    
    # Compare scroll positions
    if scroll_pos_init >= scroll_pos_end:
        break
    
    # Update the initial scroll position
    scroll_pos_init = scroll_pos_end
    time.sleep(3)
    # Get the page source after scrolling
    page_source = driver.page_source
    
    # Parse the page source using Selectolax
    parsed = HTMLParser(page_source)
    
    # Extract desired data using Selectolax methods
    articles = parsed.css("article[class='table-row show js-table-row js-show has-live-tv-link']")
    channels = []
    for article in articles:
        try:
            channel = article.css_first("div[class='cell channel'] a").attrs.get("title")
        except: channel =None
        time_cell = article.css_first("div[class='cell time']")
        time_range = time_cell.css_first("p.lapse").text()
        start_time, end_time = time_range.split(" - ")
        day = time_cell.css_first("p.date").text()
        program = article.css_first("p[class = 'h7']").text()
        try:
            description = article.css_first("p[class = 'small-meta description children-info']").text()
        except:
            description = None
        try:
            subgenre  = article.css_first("div[class = 'cell genre'] p").text()
        except:
            subgenre = None
        try:
            genre  = article.css_first("div[class = 'cell category'] p").text()
        except:
            genre = None
        try:
            #program_l = article.css_first("p[class = 'h7']")
            live  = article.css("span[data-style = 'elements/tv-show-mark']")[-1].text()
        except:
            live = None

        now = datetime.datetime.now()
        date_scraped = now.strftime("%d/%m/%Y %H:%M:%S")
        
        print(channel, "|",  time_range, "|", day, "|", program, "|", description, "|", subgenre, "|", genre, "|", live)


        sql = "INSERT IGNORE INTO data_table (channel, start_time, end_time, day, program, description, subgenre, genre, live, date_scraped) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values = (channel, start_time, end_time, day, program, description, subgenre, genre, live, date_scraped)
        mycursor.execute(sql, values)
    
# Close the webdriver
driver.quit()

#%%


# Select unique records from the table
select_query = "SELECT DISTINCT * FROM data_table"

mycursor.execute(select_query)
result = mycursor.fetchall()

# Create a DataFrame from the selected records
df = pd.DataFrame(result, columns=["channel", "start_time", "end_time", "day", "program", "description", "subgenre", "genre", "live", "date_scraped"])

# Specify the CSV file path
csv_file_path = "output.csv"

# Export the DataFrame to a CSV file
df.to_csv(csv_file_path, index=False)

# Print a message indicating the successful export
print("Data exported to CSV file:", csv_file_path)

# %%
