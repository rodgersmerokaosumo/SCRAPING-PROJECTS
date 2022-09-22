from requests_html import HTMLSession
s = HTMLSession()
url = f'https://kw.pricena.com/en/tv-video/tv/page/1?ref=quicklinks'
r = s.get(url)