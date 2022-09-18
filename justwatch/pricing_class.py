class Pricing:
    def __init__(self, soup_object):
        self.soup_object = soup_object

    def get_stream_options(self):
        stream_list = []
        price_comparison = self.soup_object.find("div", {"class":"price-comparison--block"})
        price_comparison_stream = price_comparison.find_all("div", {"class":"price-comparison__grid__row price-comparison__grid__row--stream price-comparison__grid__row--block"})
        for comp in price_comparison_stream:
            comp = comp.find_all("div", {"class":"price-comparison__grid__row__element"})
            for comp in comp:
                service = comp.find("img")
                service = service['title']
                pricing = comp.find("div", {"class":"price-comparison__grid__row__price"}).text.replace('\n',"")
                stream_options = {service:pricing}
                stream_list.append(stream_options)


        return stream_list


    def get_rent_options(self):
        rent_list = []
        price_comparison = self.soup_object.find("div", {"class":"price-comparison--block"})
        price_comparison_rent = price_comparison.find_all("div", {"class":"price-comparison__grid__row price-comparison__grid__row--rent price-comparison__grid__row--block"})
        for comp in price_comparison_rent:
            comp =  comp.find_all("div", {"class":"price-comparison__grid__row__element"})
            for element in comp:
                service = element.find("img")
                service = service['title']
                pricing = element.find("div", {"class":"price-comparison__grid__row__price"}).text.replace('\n',"")
                rent_options = {service:pricing}
                rent_list.append(rent_options)
        
        return rent_list

    def get_buy_options(self):
        buy_list = []
        price_comparison = self.soup_object.find("div", {"class":"price-comparison--block"})
        price_comparison_buy = price_comparison.find_all("div", {"class":"price-comparison__grid__row price-comparison__grid__row--buy price-comparison__grid__row--block"})
        for comp in price_comparison_buy:
            comp = comp.find_all("div", {"class":"price-comparison__grid__row__element"})
            for element in comp:
                service = element.find("img")
                service = service['title']
                pricing = element.find("div", {"class":"price-comparison__grid__row__price"}).text.replace('\n',"")
                buy_options = {service:pricing}
                buy_list.append(buy_options)
                
        return buy_list
