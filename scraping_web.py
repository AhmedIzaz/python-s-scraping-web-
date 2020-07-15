import requests, re, sys, logging, csv
from html import unescape


def get_page_content(url):
    try:
        response = requests.get(url)
    except requests.RequestException as eRror:
        logging.error(eRror)
    if response.ok:
        return response.text
    logging.error("can't get content from"+url)
    return ""

def get_category_list(content):
    category_list = category_pat.findall(content)
    #it will return a tuple where 2 item(cate_url and cate_name) in list
    return category_list

def get_next_page(category_url, content):
    result = next_pat.findall(content)
    if len(result)==0:
        return None
    i = category_url.rfind("/")
    return category_url[0:i+1]+result[0]

def get_book_list(content):
    content = content.replace("\n", " ")
    return book_list_pat.findall(content)

def get_product_info(content):
    base_url = "http://books.toscrape.com"
    img_result = image_url_pat.findall(content)
    if len(img_result)==0:
        logging.warn("Image url is not found!")
        image_url = ""
    else:
        img_url = img_result[0]
        img_url = img_url.replace("../../", "")
        image_url = base_url + img_url

    description_result = description_pat.findall(content)
    if len(description_result)==0:
        logging.warn("Description is not found")
        description = ""
    else:
        description = unescape(description_result[0])
    
    price_result = price_pat.findall(content)
    if len(price_result)==0:
        logging.warn("price are not included here!")
        price = ""
    else:
        price = price_result[0]

    upc_result = upc_pat.findall(content)
    if len(upc_result)==0:
        logging.warn("UPC are not included here!")
        upc = ""
    else:
        upc = upc_result[0]

    availability_result = availability_pat.findall(content)
    if len(availability_result)==0:
        logging.warn("this book is not available right now!")
        availability = ""
    else:
        availability = availablity_result[0]

    return upc, price, image_url, availability, description

def scrape_book_info(book_info, category_name):
    book_url, book_name = book_info
    book_name = unescape(book_name)
    book_dict = {"Name": book_name, "Category": category_name}
    book_url = book_url.replace("../../../", "")
    book_url = "http://books.toscrape.com/catalogue" + book_url

    book_dict["URL"] = book_url

    print("Scraping book", book_name)
    logging.info("Scraping:"+book_url)

    content = get_page_content(book_url)
    content = content.replace("\n", " ")

    upc, price, image_url, availability, description = get_product_info(content)
    book_dict["UPC"] = upc
    book_dict["ImageURL"] = image_url
    book_dict["Price"] = price
    book_dict["Availability"] = availability
    book_dict["Description"] = description
    
    csv_writer.writerow(book_dict)


def crawl_category(category_name, category_url):
    while True:
        content = get_page_content(category_url)
        book_list = get_book_list(content)

        for book in book_list:
            scrape_book_info(book, category_name)
        next_page = get_next_page(category_url, content)
        if next_page is None:
            break
        category_url = next_page

def crawl_website():
    url = "http://books.toscrape.com/index.html"
    domain = "books.toscrape.com"
    content = get_page_content(url)
    if content== "":
        logging.critical("got null content from "+url)
        sys.exit(1)
    
    categories = get_category_list(content)

    for category in categories:
        category_url, category_name = category
        category_url = "http://"+domain+"/"+category_url
        crawl_category(category_name, category_url)



if __name__ == "__main__":
    #it will return a tuple where 2 item(cate_url and cate_name) in list
    category_pat = re.compile(r'<li>\s*<a href="(catalogue/category/books/.*?)">\s*(\w+[\s\w]+\w)\s*?<', re.M | re.DOTALL)

    book_list_pat = re.compile(r'<h3><a href="(.*?)" title="(.*?)">')
    
    upc_pat = re.compile(r'<th>UPC</th><td>(.*?)</td>')
    
    image_url_pat = re.compile(r'<div class="item active">\s*<img src="(.*?)"', re.M | re.DOTALL)
    
    price_pat = re.compile(r'<th>Price (incl. tax)</th><td>([\D\d.]+?)</td>')
    
    availability_pat = re.compile(r'<th>Availability</th>\s*<td>(.*?)</td>', re.M | re.DOTALL)
    
    description_pat = re.compile(r'<div id="production_description" class="sub-header">.*?<p>(.*?)</p>', re.M | re.DOTALL)
    
    #the last regex
    next_pat = re.compile(r'<li class="next"><a href="(.*?)">next</a></li>')


    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%d-%m-%Y %I-%M-%S %p', filename='web_scrape.log', level=logging.DEBUG)

    with open('scrape_web.csv', 'w') as csvf:
        csv_writer = csv.DictWriter(csvf, fieldnames=["Name", "Category", "URL", "UPC", "ImageURL", "Price", "Availability", "Description"])
        csv_writer.writeheader()

        crawl_website()
        print("Crawling Done!")