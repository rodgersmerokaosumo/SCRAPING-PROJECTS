#%%
import httpx
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
ua = UserAgent()
header = {'User-Agent':str(ua.random)}
print(header)


#%%
url = "https://www.jumia.ma/tvs/"

#%%
resp = httpx.get(url, headers=header)

html = HTMLParser(resp.text)

print(html.css_first("a[aria-label = 'Next page']"))
# %%
