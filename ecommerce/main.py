import requests
from bs4 import BeautifulSoup
import pandas as pd

headers = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

#%%
base_url = 'https://www.thewhiskyexchange.com'
productlinks = []
for x in range(1,5):
    r = requests.get(f'https://www.thewhiskyexchange.com/search?q=JAPANESE+WHISKEY&pg={x}')
    soup = BeautifulSoup(r.content, 'lxml')

    productlist = soup.find('div', class_ = 'product-grid')
    productlist = productlist.find_all('li', class_ = 'product-grid__item')

    for item in productlist:
        for link in item.find_all('a', href = True):
            productlinks.append(base_url + link['href'])
            
#%%          
#testlink = 'https://www.thewhiskyexchange.com/p/50479/ichiros-malt-double-distilleries-2021'
whiskylist = []
for link in productlinks[:4]:
    r = requests.get(link, headers=headers)
    soup = BeautifulSoup(r.content, 'lxml')
    name = soup.find('h1', class_ = 'product-main__name').text.strip()
    try:
        rating = soup.find('div', class_ = 'review-overview').text.strip()
    except:
        rating = 'No rating'
    inStock = soup.find('p', class_ = 'product-action__stock-flag').text.strip()
    meta = soup.find('ul', class_ = 'product-main__meta').text.strip()
    price = soup.find('p', class_ = 'product-action__price').text.strip()
    content = soup.find('p', class_ = 'product-main__data').text.strip()
    
    whisky = {
        'name':name,
        'rating':rating,
        'inStock':inStock,
        'price':price,
        'metadata':meta,
        'alc content':content,
        'scrape link':link
        
    }

    whiskylist.append(whisky)
    print('Saving: ', whisky['name'])

# %%

df = pd.DataFrame(whiskylist)
print (df['alc content'].head(15))