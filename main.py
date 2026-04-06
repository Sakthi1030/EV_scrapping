import asyncio
import logging
import os
import sys
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv
from config import BASE_URL, EXTRACTION_MODE, REQUIRED_KEYS, SCRAPER_ENGINE
from utils.data_utils import save_ev_to_csv
from utils.scraper_utils import fetch_and_process_page

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

PROJECT_ROOT = Path(__file__).resolve().parent


def configure_runtime() -> None:
    """
    Keep Crawl4AI artifacts local to the project and avoid Windows console encoding crashes.
    """
    os.environ.setdefault("CRAWL4_AI_BASE_DIRECTORY", str(PROJECT_ROOT))

    if os.name == "nt":
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name, None)
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")

async def crawl_ev_scooters():
    """
    Main function to crawl EV scooter data from the website.
    """
    page_number = 1
    all_evs = []
    seen_names = set()

    async with AsyncWebCrawler(base_directory=str(PROJECT_ROOT), verbose=False) as crawler:
        while True:
            evs, no_results_found = await fetch_and_process_page(
                crawler,
                page_number,
                BASE_URL,
                REQUIRED_KEYS,
                seen_names,
                extraction_mode=EXTRACTION_MODE,
                scraper_engine=SCRAPER_ENGINE,
            )

            if no_results_found:
                print("No more EV scooters found. Ending crawl.")
                break  # Stop if no more results

            if not evs:
                print(f"No EVs extracted from page {page_number}.")
                break  # Stop if no EVs found

            all_evs.extend(evs)
            page_number += 1

            await asyncio.sleep(2)  # Be polite to the website

    if all_evs:
        save_ev_to_csv(all_evs, "ev_scooters.csv")
    else:
        print("No EV scooters found during the crawl.")

async def main():
    configure_runtime()
    try:
        await crawl_ev_scooters()
    except RuntimeError as exc:
        logging.error(str(exc))

if __name__ == "__main__":
    asyncio.run(main())

