BASE_URL = "https://www.bikedekho.com/electric-scooters"

SCRAPER_ENGINE = "crawl4ai"
EXTRACTION_MODE = "css"
DEEPSEEK_PROVIDER = "deepseek/deepseek-chat"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"

REQUIRED_KEYS = [
    "name",
    "speed",
    "range",
    "rating",
    "reviews",
    "price",
    "emi",
    "extra_details",
]
