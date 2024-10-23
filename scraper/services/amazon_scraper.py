import logging

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from products.models import Brand, Product
from scraper.services.proxy import get_random_proxy

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "max-age=0",
    "device-memory": "8",
    "downlink": "1.4",
    "dpr": "1.25",
    "ect": "3g",
    "priority": "u=0, i",
    "rtt": "300",
    "sec-ch-device-memory": "8",
    "sec-ch-dpr": "1.25",
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-ch-ua-platform-version": "\"10.0.0\"",
    "sec-ch-viewport-width": "1042",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "viewport-width": "1042"
}
logger = logging.getLogger('scraping')


class AmazonSpider(scrapy.Spider):
    name = "amazon_data"

    # Corrected constructor
    def __init__(self, brand, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.brand = brand

    def start_requests(self):
        url = f'https://www.amazon.com/s?k={self.brand}&crid=2K5HA2CNE4A8S&sprefix=step+2%2Caps%2C165&ref=nb_sb_noss_1'
        meta = {'proxy': get_random_proxy(), 'brand': self.brand}
        yield scrapy.Request(
            url,
            headers=HEADERS, meta=meta)

    def parse(self, response, **kwargs):
        for url in response.css("h2 > a.a-link-normal::attr(href)").getall():
            url = url.split('?')[0]
            meta = {'proxy': get_random_proxy(), 'brand': response.meta.get('brand')}

            yield response.follow(url, callback=self.parse_details, headers=HEADERS, meta=meta)

        next_page_url = response.css("a.s-pagination-next::attr(href)").get()
        if next_page_url:
            next_page_url = next_page_url.split('&xpid')[0]
            meta = {'proxy': get_random_proxy(), 'brand': response.meta.get('brand')}

            yield response.follow(next_page_url, callback=self.parse, meta=meta, headers=HEADERS)

    def parse_details(self, response, **kwargs):
        try:
            product_name = response.css('span#productTitle::text').get('').strip()
            asin = response.css("th:contains('ASIN') + td::text").get('').strip()
            image_url = response.css('div#imgTagWrapperId>img::attr(src)').get('').strip()
            brand_name = response.meta.get('brand')
            self.save_product_to_db(brand_name, product_name, asin, image_url, response.url)
            logger.info(f"Successfully scraped product {product_name} (ASIN: {asin}) for brand {brand_name}")
        except Exception as e:
            logger.error(f"Error scraping product for brand {response.meta.get('brand')}: {e}")

    def save_product_to_db(self, brand_name, product_name, asin, image_url, product_url):
        try:
            # Ensure that none of the critical fields are empty
            if not product_name or not asin or not image_url:
                logger.warning(
                    f"Skipping product with missing data (Name: {product_name}, ASIN: {asin}, Image: {image_url})")
                return  # Skip saving if any of the required data is missing

            # Get or create the Brand object
            brand, _ = Brand.objects.get_or_create(name=brand_name)

            # Check if a product exists either by ASIN or by product name (for that brand)
            product = Product.objects.filter(asin=asin).first() or Product.objects.filter(name=product_name,
                                                                                          brand=brand).first()
            if product:
                product.asin = asin
                product.name = product_name
                product.image = image_url
                product.brand = brand
                product.save()
                logger.info(
                    f"Product '{product_name}' (ASIN: {asin}) updated in the database for brand '{brand_name}'.")
            else:
                # Create a new product if it doesn't exist
                Product.objects.create(
                    name=product_name,
                    asin=asin,
                    image=image_url,
                    brand=brand,
                    sku=None,
                )
                logger.info(
                    f"Product '{product_name}' (ASIN: {asin}) created in the database for brand '{brand_name}'.")

        except Exception as e:
            logger.error(f"Error saving product to the database: {e}")


def scrape_amazon_brand(brand_name):
    # Get project settings
    local_setting = get_project_settings()

    # Customize settings
    file_name = f"{brand_name}_products.json"
    local_setting.set('BOT_NAME', 'amazon')
    local_setting['FEED_FORMAT'] = 'json'
    local_setting['FEED_URI'] = file_name
    local_setting['CONCURRENT_REQUESTS'] = 5
    local_setting['ROBOTSTXT_OBEY'] = False
    local_setting['DOWNLOAD_DELAY'] = 2
    local_setting['RETRY_TIMES'] = 10

    local_setting['RETRY_HTTP_CODES'] = [500, 502, 503, 504, 400, 403, 404, 408]
    local_setting[
        'USER_AGENT'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
    local_setting['LOG_LEVEL'] = 'DEBUG'
    # Enable caching
    local_setting['HTTPCACHE_ENABLED'] = True
    local_setting['HTTPCACHE_EXPIRATION_SECS'] = 3600  # Cache expiration (1 hour)
    local_setting['HTTPCACHE_DIR'] = 'httpcache'  # Directory for cache
    local_setting['HTTPCACHE_IGNORE_HTTP_CODES'] = [500, 502, 503, 504, 400, 403, 404, 408]  # Ignore these codes

    # Initialize and start CrawlerProcess with the custom settings
    process = CrawlerProcess(local_setting)
    crawler = process.create_crawler(AmazonSpider)
    # Start the crawler, passing the brand name as an argument
    process.crawl(crawler, brand=brand_name)
    process.start()
