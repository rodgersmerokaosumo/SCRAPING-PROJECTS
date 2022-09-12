from time import sleep
from requests_html import HTMLSession

#%%
def getPrice(url):
    s = HTMLSession()
    r = s.get(url)
    r.html.render(sleep=1)
    
    product = {
        'title': r.html.xpath('//*[@id="productTitle"]', first = True).text,
        'price': r.html.xpath('//*[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span[2]/span[1]', first = True).text
        
    }
    
    print(product)
    return product


getPrice('https://www.amazon.co.uk/gp/product/B0006H92QK/ref=as_li_tl?ie=UTF8&tag=jwr-yt-21&camp=1634&creative=6738&linkCode=as2&creativeASIN=B0006H92QK&linkId=1344df813fc1edd259626cd126449726&th=1')