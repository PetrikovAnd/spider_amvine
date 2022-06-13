import scrapy
import json
from pprint import pprint
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re
from datetime import datetime
import time


class AmvineRuSpider(scrapy.Spider):
    name = 'amvine.ru'
    allowed_domains = ['amwine.ru']
    start_urls = [ 'https://amwine.ru/catalog/krepkie_napitki/konyak/filter/country-is-rossiya/?page=1', 'https://amwine.ru/catalog/pivo/light/?page=1']
    
    
    def parse(self, response):
        quantity = re.findall(r"productsTotalCount = [^;]+", response.xpath('//*[@id="fix-search"]/script[28]/text()').get())
        quantity = int(quantity[0].split(' ')[-1])
        next_page = ''
        #quantity //= 18
        number_page = int(response.url.split('?page=')[-1])
        if number_page*18<quantity:
            number_page += 1
            next_page = f'{response.url.split("?page=")[0]}?page={number_page}'
        urls = re.findall(r".catalog[^']+", response.xpath('//*[@id="fix-search"]/script[28]/text()').get().replace('window.products = ', '').replace('\n','').replace('true','True').replace('false' ,'False').split('window.catalogPriceCode')[0].strip())
        for val in urls:
            yield response.follow(f'https://amwine.ru{val}', callback=self.parse_card)
        if next_page != '':
            yield response.follow(next_page, callback=self.parse)

        
            
    def parse_card(self, response):
        print('       ')
        print('       ')
        print(response.url)
        print('       ')
        print('       ')
        sale_tag = ''
        meta = {}
        tags = []
    
        if response.css('div.catalog-element-info__title h1::text').get() is None:
            title = 'N/A'
        else:
            title = response.css('div.catalog-element-info__title h1::text').get().strip()
            if 'Цвет' in  response.css('div.h4::text').extract():
                index = response.css('div.h4::text').extract().index('Цвет')
                color = response.xpath(f'//*[@id="about-drink"]/div/div[2]/div[1]/div[2]/div[{index}]/p/text()').get().replace('\r\n','')
                title = f'{title}, {color}'
            
        if response.xpath('//*[@id="catalog-element-main"]/div[2]/div/div[1]/div/@data-brand').get() in [None, '']:
            brand = 'N/A'
        else:
            brand = response.xpath('//*[@id="catalog-element-main"]/div[2]/div/div[1]/div/@data-brand').get().strip()
        try:
            current = float(re.findall(r'price. .[^"]+', response.xpath('//*[@id="fix-search"]/script[25]/text()').get())[0].replace('price: "',''))
        except:
            current = 'N/A'
        try:
            original = float(re.findall(r'priceWithDiscount. .[^"]+', response.xpath('//*[@id="fix-search"]/script[25]/text()').get())[0].replace('priceWithDiscount: "',''))
        except:
            original = current
     
        try:
            if original != current:
                sale_tag =round((100*(1 - current/original)),1)
                sale_tag = f'Скидка {sale_tag}%'
        except:
            None
        
        try:
            tags = list(map(lambda s: s.strip(), response.css('div.tag-wrapper span ::text').getall()))
        except:
            None
        
        in_stock = response.css('div.catalog-element-info__not-in-stock ::text').get() != 'Нет в наличии'
        try:
            main_image = (re.findall(r'pictureUrl. .[^"]+', response.xpath('//*[@id="fix-search"]/script[25]/text()').get())[0].replace('pictureUrl: "',''))
        except:
            main_image = 'N/A'
        try:
            meta['АРТИКУЛ'] = response.css('div.catalog-element-info__article span::text').get().strip().replace('  ','').split('Артикул: ')[1]
        except:
            None
        meta_list = response.css('div.h4::text').extract()
        del meta_list[0]
        del meta_list[0]
        for val in meta_list:
            if val != 'Смотрите также' and val != 'Описание':
                index = response.css('div.h4::text').extract().index(val)-1
                meta[val.upper()] = str(response.xpath(f'//*[@id="about-drink"]/div/div[2]/div[1]/div[2]/div[{index}]/p/text()').get()).replace('\r\n','')
            elif val == 'Описание':
                index = response.css('div.h4::text').extract().index(val)-1
                meta['__description'] = str(response.xpath(f'//*[@id="about-drink"]/div/div[2]/div[1]/div[2]/div[{index}]/p/text()').get()).replace('\r\n','')
        for val in response.css('div.about-wine__param span.about-wine__param-title::text').extract():
            index = 1 + response.css('div.about-wine__param span.about-wine__param-title::text').extract().index(val)
            try:
                meta[val.strip().upper()] = response.xpath(f'//*[@id="about-drink"]/div/div[1]/div[{index}]/span[2]/a/text()').get().strip().replace('   ','').replace('  ',' ')
            except:
                meta[val.strip().upper()] = response.xpath(f'//*[@id="about-drink"]/div/div[1]/div[{index}]/span[2]/text()').get().strip().replace('   ','').replace('  ',' ')
        yield {
            'timestamp': datetime.now(),
            'rpc': response.xpath('//*[@id="catalog-element-main"]/div[2]/div/div[1]/div/@data-id').get().strip(),
            'url': response.url,
            'title': title,
            'marketing tags': tags,
            'brand': brand,
            'section':response.xpath('//*[@id="catalog-element-main"]/div[2]/div/div[1]/div/@data-category').get().strip().split('/'),
            'price_data' : {
                'current': current,
                'original': original,
                'sale_tag':sale_tag
                 },
            'stock':{
                'in_stock': in_stock,
                'count':0
                },
            'assets':{
                'main_image': f'https://amwine.ru{main_image}',
                'set_images': [f'https://amwine.ru{main_image}'],
                'view360':[],
                'video':[]
                },
            'metadata':meta,
            'variants':1
            }
    

        