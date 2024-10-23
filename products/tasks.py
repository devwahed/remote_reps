import logging

from celery import shared_task

from scraper.services.amazon_scraper import scrape_amazon_brand
from .models import Brand

logger = logging.getLogger('scraping')


@shared_task(bind=True)
def scrape_products_for_brand(self):
    """
    Scrapes product data for all brands stored in the database.
    """
    logger.info('Starting product scraping task for all brands...')
    brands = Brand.objects.all()  # Fetch all brands

    for brand in brands:
        try:
            logger.info(f'Starting scraping for brand: {brand.name}')
            scrape_amazon_brand(brand.name)
            logger.info(f'Successfully scraped products for brand: {brand.name}')
        except Exception as e:
            logger.error(f'Error occurred while scraping for brand {brand.name}: {str(e)}')
    logger.info('Finished scraping task for all brands.')
