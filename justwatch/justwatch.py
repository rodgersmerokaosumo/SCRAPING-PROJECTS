from requests_html import  HTML, HTMLSession
session = HTMLSession()
url = "https://www.justwatch.com/us/movies?genres=act&release_year_from=2022"
r = session.get(url)
r = r.html.render(scrolldown=5)
print(r.html.find("div.title-list-grid__item"))