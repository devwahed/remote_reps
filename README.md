# Amazon Brand Product Scraper with Django, Celery, and Scrapy

## Table of Contents
- [Objective](#objective)
- [Features](#features)
- [Setup and Run the Project Locally](#setup-and-run-the-project-locally)
  - [Prerequisites](#prerequisites)
  - [Step 1: Install Dependencies](#step-1-install-dependencies)
  - [Step 2: Install Redis](#step-2-install-redis)
  - [Step 3: Set Up Django](#step-3-set-up-django)
- [Celery and Broker Setup](#celery-and-broker-setup)
  - [Step 1: Configure Celery](#step-1-configure-celery)
  - [Step 2: Start Celery Worker](#step-2-start-celery-worker)
  - [Step 3: Start Celery Beat](#step-3-start-celery-beat)
- [Scheduling and Managing Periodic Tasks](#scheduling-and-managing-periodic-tasks)
- [Web Scraping Implementation](#web-scraping-implementation)
- [Assumptions and Design Decisions](#assumptions-and-design-decisions)

## Objective

This project is a Django-based system that scrapes and lists all products of a specific Amazon brand. The system is integrated with Celery to automate the scraping process and update the product list four times a day. It gathers the following information for each product:
- Product Name
- ASIN (Amazon Standard Identification Number)
- SKU
- Image URL

## Features

- **Django Admin Setup**: Manage Amazon brands through the Django admin interface.
- **Web Scraping**: Scrapes product data from Amazon based on a brand’s page.
- **Celery Integration**: Automates the scraping process with scheduled tasks (four times daily).
- **Error Logging and Retry Mechanisms**: Ensures scraping resilience through retries and logs.

---

## Setup and Run the Project Locally

### Prerequisites
- Python 3.10
- Django
- Celery
- Redis (message broker for Celery)
- Scrapy (for web scraping)

### Step 1: Install Dependencies

To install the required packages from the `requirements.txt` file, run:

```bash
pip install -r requirements.txt
```

### Step 2: Install Redis

1. **Download Redis for Windows**:
   - Download Redis-x64-5.0.14.1.msi from the [Redis GitHub Releases](https://github.com/tporadowski/redis/releases).

2. **Run Redis**:
   - Open the folder and run `redis-cli.exe`. In the Redis CLI, type `PING` to check if Redis is working:
     ```bash
     PING
     ```
   - If Redis is working correctly, it will return `PONG`.

### Step 3: Set Up Django

1. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create a Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

3. **Run the Django Development Server**:
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000` to access the site.

---

## Celery and Broker Setup

### Step 1: Configure Celery

Celery settings are configured in the `settings.py` file, using Redis as the broker:

```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULE = {
    'scrape-amazon-products-every-6-hours': {
        'task': 'products.tasks.scrape_products_for_brand',
        'schedule': crontab(hour='*/6'),
    },
}
CELERY_TIMEZONE = 'UTC'
```

### Step 2: Start Celery Worker

In a new terminal, start the Celery worker:

```bash
celery -A amazon worker --pool=solo --loglevel=info
```

### Step 3: Start Celery Beat

In another terminal, start the Celery Beat scheduler to handle task scheduling:

```bash
celery -A amazon beat --loglevel=info
```

---

## Scheduling and Managing Periodic Tasks

Celery Beat is used to schedule tasks, running the scraper every 6 hours. The schedule is defined in `settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'scrape-amazon-products-every-6-hours': {
        'task': 'products.tasks.scrape_products_for_brand',
        'schedule': crontab(hour='*/6'),
    },
}
```

Once both the Celery worker and Celery Beat are running, product scraping will automatically occur every 6 hours.

---

## Web Scraping Implementation

The project uses **Scrapy** to scrape product data from Amazon based on a brand’s page.

### Key Components:
- **Spider (`AmazonSpider`)**: Scrapy spider that scrapes product data such as product name, ASIN, SKU, and image URL.
- **Pagination Handling**: The spider scrapes all pages of a brand’s products.
- **Headers and Proxies**: Custom headers and rotating proxies are used to avoid detection.
- **Retries and Delays**: Retry mechanisms for HTTP errors and delays to mimic human-like behavior.

### How the Scraper Works:
1. **Brand Input**: The brand name is passed to the Scrapy spider.
2. **Request Handling**: Scrapy sends requests to Amazon’s search page using the brand name.
3. **Product Data Parsing**: The page content is parsed to extract product details.
4. **Pagination**: The spider scrapes all available products by handling pagination.
5. **Database Update**: Scraped data is stored in the database. Existing products are updated based on ASIN.

---

## Assumptions and Design Decisions

- **ASIN-Based Updates**: Products are uniquely identified by their ASIN. If a product already exists in the database, it is updated rather than creating a new entry.
- **Anti-Scraping Measures**:
  - **User-Agent Rotation** and **Proxy Rotation**: Prevents scraping blocks by rotating User-Agents and proxies.
  - **Delays**: Mimics human browsing behavior to avoid detection.
- **Error Handling**: Robust error logging and retry mechanisms are in place to ensure smooth scraping and task execution.

---

