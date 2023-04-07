#%%
import httpx
from selectolax.parser import HTMLParser

url = "https://www.123comparer.be/Televiseur/"
base_url = "https://www.123comparer.be"

#%%
def get_links(url):
    resp = httpx.get(url).text
    r = HTMLParser(resp)
    links = r.css("p[class = 'oldH3'] a")
    for link in links:
        tv_link = base_url + link.attrs["href"]
        print(tv_link)
    next_page = r.css("div[id = 'pagination'] a")
    next_page = base_url+ next_page[-1].attrs["href"]
    print(next_page)
    return next_page

#%%
while True:
    url = get_links(url)