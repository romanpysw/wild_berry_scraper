from selenium import webdriver
from bs4 import BeautifulSoup as bs
import re
import os
import csv
import requests
import asyncio
import time

url_wild = 'https://www.wildberries.ru/catalog/elektronika/planshety'

wFile = open("wild_res.csv", mode = "w", encoding = 'utf-8')
names = ["Наименование", "Цена со скидкой", "Цена без скидки", "Описание", "Характеристики", 
        "Производитель", "Ссылка на производителя", 
        "Ссылки на картинки", "Имена картинок"]
file_writer = csv.DictWriter(wFile, delimiter = ';', lineterminator = '\n', fieldnames = names)
file_writer.writeheader()

try:
    os.mkdir('img')
except Exception as e:
    print(e)
    pass

def get_category_page_product_urls_wild(category_page_url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    driver = webdriver.Chrome(
        executable_path=os.getcwd() + '/chromedriver.exe', 
        options=options
    )

    product_urls = list()

    try:
        driver.get(category_page_url)
        bso = bs(driver.page_source, 'html.parser')
        product_objs = bso.find_all('div', {'class': 'product-card j-card-item'})

        for product in product_objs:
            product_urls.append(product.find('a')['href'])

    except Exception as e:
        print(e)
    finally:
        driver.delete_all_cookies()
        driver.close()
        driver.quit()
        return product_urls

async def parse_product_wild(product_url):
    
    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(None, requests.get, product_url)
    response = await future

    print(response.status_code)

    good_specs = list()
    good_photo_urls = list()
    photo_names = list()

    bso = bs(response.content, 'html.parser')

    try:
        name = bso.find('h1', {'class': 'same-part-kt__header'}).text
    except Exception as e:
        name = 'no_data'
        print(e)

    try:
        dirname = re.sub('[^A-Za-z0-9А-Яа-я]', '_', name)
        os.mkdir('img/' + dirname)
    except Exception as e:
        print(e)
        pass

    try:
        fin_price = bso.find('span', {'class': 'price-block__final-price'}).text
    except Exception as e:
        fin_price = 'no_data'
        print(e)
    
    try:
        old_price = bso.find('del', {'class': 'price-block__old-price j-final-saving'}).text
    except Exception as e:
        old_price = 'no_data'
        print(e)

    try:
        descript = bso.find('div', {'class': 'collapsable__content j-description'}).find('p').text
    except Exception as e:
        descript = 'no_data'
        print(e) 
    
    try:
        specs = bso.find_all('tbody')
        for spec in specs:
            good_specs.append(spec.find('span').text + str('-') + spec.find('td').text)
    except Exception as e:
        good_specs.append('no_data')
        print(e) 

    try:
        customer = bso.find('div', {'class': 'same-part-kt__brand-logo hide-desktop'}).find('a')['title']
    except Exception as e:
        customer = 'no_data'
        print(e)

    try:
        customer_url = bso.find('div', {'class': 'same-part-kt__brand-logo hide-desktop'}).find('a')['href']
    except Exception as e:
        customer_url = 'no_data'
        print(e)

    try:
        photo_urls = bso.find('ul', {'class': 'swiper-wrapper'}).find_all('li')

        for photo_url in photo_urls:
            good_photo_urls.append('https:' + photo_url.find('div').find('img')['src'])

            photo_names.append(good_photo_urls[len(good_photo_urls) - 1][good_photo_urls[len(good_photo_urls) - 1].rfind('/'):])

            img_data = requests.get(good_photo_urls[len(good_photo_urls) - 1]).content

            with open('img/'+ dirname + '/' + photo_names[len(photo_names) - 1], 'wb') as fw:
                fw.write(img_data)

    except Exception as e:
        good_photo_urls.append('no_data')
        print(e)
        

    file_writer.writerow({"Наименование": name, "Цена со скидкой": fin_price, "Цена без скидки": old_price, 
            "Описание": descript, "Характеристики": good_specs,
            "Производитель": customer, "Ссылка на производителя": customer_url, 
            "Ссылки на картинки": good_photo_urls, "Имена картинок": photo_names})

async def main(url_list):
    tasks = [asyncio.create_task(parse_product_wild(url)) for url in url_list]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(get_category_page_product_urls_wild(url_wild)))
    print("By " + str(time.time() - start_time) + " seconds")