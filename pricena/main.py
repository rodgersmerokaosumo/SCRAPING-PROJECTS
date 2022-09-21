#%%
from unicodedata import category
from requests_html import HTMLSession

s = HTMLSession()

#%%
def get_produdt_links(page):
    url = f'https://themes.woocommerce.com/storefront/product-category/clothing/page/{page}'
    links = []
    r = s.get(url)
    products = r.html.find('ul.products.columns-4 li')
    for item in products:
        links.append(item.find('a', first = True).attrs['href'])
    return links

page1 = get_produdt_links(1)
#print(page1)

# %%

test_link = 'https://themes.woocommerce.com/storefront/product/lowepro-slingshot-edge-250-aw/'

r = s.get(test_link)

title = r.html.find('h1.product_title.entry-title', first = True).text.strip()
price = r.html.find('p.price', first = True).text.strip()
sku = r.html.find('span.sku_wrapper', first = True).text.strip()
category = r.html.find('span.posted_in', first = True).text.strip()
print(title, price, sku, category)