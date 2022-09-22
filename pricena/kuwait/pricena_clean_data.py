#%%
import mysql.connector
import pandas as pd


#%%
pricena_tv_kuwait_db = mysql.connector.connect(
  host="localhost",
  user="root",
  password="4156"
)

#%%
##connect to db
from sqlalchemy import create_engine

# Credentials to database connection
hostname="localhost"
dbname="pricena_tv_kuwait_db"
uname="root"
pwd="4156"

# Create SQLAlchemy engine to connect to MySQL Database
engine = create_engine("mysql+pymysql://{user}:{pw}@{host}/{db}"
				.format(host=hostname, db=dbname, user=uname, pw=pwd))

mycursor = pricena_tv_kuwait_db.cursor(buffered=True)

#%%
mycursor.execute("use pricena_tv_kuwait_db")

#%%
df = pd.read_sql('SELECT * FROM data_table', con=engine)
df.head()

#%%

df['specifications'] = df['specifications'].apply(lambda x : dict(eval(x)) )
spec_df = df['specifications'].apply(pd.Series )
df = pd.concat([df, spec_df.reindex(df.index)], axis=1)
df_l  = pd.concat([df[['Country Code', 'category','title', 'brand','number_of_offers', 'average_price', 'currency',  'price', 'scrape_date', 'scrape_link']], spec_df.reindex(df.index)], axis=1)
df_l.head()


#%%
df_long = df_l.set_index(['Country Code',  'brand', 'Model#', 'title', 'number_of_offers', 'average_price', 'currency', 'Date added', 'category' , 'scrape_date','scrape_link']).stack().reset_index()
df_long

dict = {'level_11': 'Specification',
        0: 'Specification Value'}
 
# call rename () method
df_long.rename(columns=dict,
          inplace=True)

#%%
df_long.to_sql('data_table_clean', engine, if_exists='replace', index=False)
# %%
df_long.to_csv('pricena_kuwait_clean.csv')
# %%
