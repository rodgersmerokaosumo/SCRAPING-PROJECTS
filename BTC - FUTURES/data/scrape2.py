#%%
import yfinance as yf
import pandas as pd

stock1 = yf.Ticker('BITW')
stock2 = yf.Ticker("BTC-USD")
stock3 = yf.Ticker("^GSPC")
stock4= yf.Ticker("BTC=F")


#%%
BITW_prices = stock1.history(start="2021-01-01", end="2023-03-08")
BTC_prices = stock2.history(start="2018-01-01", end="2023-03-08")
SP500_prices = stock3.history(start="2018-01-01", end="2023-03-08")
BTCF_prices = stock4.history(start="2018-01-01", end="2023-03-08")
# %%
BITW_prices.to_csv("BITW_prices.csv")
BTC_prices.to_csv("BTC_prices.csv")
SP500_prices.to_csv("SP_prices.csv")
BTCF_prices.to_csv("BTCF_prices.csv")