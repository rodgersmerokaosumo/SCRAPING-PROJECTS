#%%
import pandas as pd
import yahoo_fin.stock_info as si
import yfinance as yf

#Crypto Prices
ticker = "BTC-USD"
#Future Ticker
f_ticker = "BTC=F"
#SP 500 perfoMANCE
s_p = "^GSPC"
shanghai = "000001.SS"

#%%



#%%
data = si.get_data(ticker, start_date="12/18/2017")
futures = si.get_data(f_ticker, start_date="12/18/2017")
sp = si.get_data(s_p, start_date="12/18/2017")
ss = si.get_data(shanghai, start_date="12/18/2017")
data.to_csv('BTC historical_data.csv')
futures.to_csv('BTC futures data.csv')
sp.to_csv('SP500 Perfomance.csv')
ss.to_csv('Shanghai delayed Index.csv')
# %%
ss.head()
# %%
