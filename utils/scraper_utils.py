import json
import os
import re
from typing import List, Set, Tuple

from bs4 import BeautifulSoup, Tag
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig, LLMExtractionStrategy

from config import DEEPSEEK_API_KEY_ENV, DEEPSEEK_PROVIDER
from models.ev_scooter import EVScooter

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def clean_text(value: str) -> str:
    return " ".join(value.split())


def extract_reviews(card: Tag) -> int:
    reviews_link = None
    for link in card.select("a[href]"):
        if "reviews" in (link.get("href") or ""):
            reviews_link = link
            break

    if not reviews_link:
        return 0

    match = re.search(r"(\d+)", reviews_link.get_text(" ", strip=True))
    return int(match.group(1)) if match else 0


def extract_rating(card: Tag) -> float:
    for span in card.select("span"):
        text = clean_text(span.get_text())
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            try:
                value = float(text)
            except ValueError:
                continue

            if 0 <= value <= 5:
                return value

    return 0.0


def extract_specs(card: Tag) -> Tuple[str, str, str]:
    specs = []
    for span in card.select("span"):
        text = clean_text(span.get_text())
        if not text:
            continue
        if any(token in text for token in ("km/Hr", "km/charge", "Hr")):
            specs.append(text)

    speed = specs[0] if len(specs) > 0 else "N/A"
    range_value = specs[1] if len(specs) > 1 else "N/A"
    extra_details = ", ".join(specs[2:]) if len(specs) > 2 else "N/A"
    return speed, range_value, extra_details


def extract_price(card: Tag) -> str:
    text = clean_text(card.get_text(" ", strip=True))
    match = re.search(r"Rs\s*[\d,]+(?:\s*\*\s*Onwards)?", text)
    return match.group(0) if match else "N/A"


def extract_emi(card: Tag) -> str:
    text = clean_text(card.get_text(" ", strip=True))
    match = re.search(r"EMI starts from\s*₹\s*[\d,]+", text)
    return match.group(0) if match else "N/A"


def get_listing_cards(soup: BeautifulSoup) -> List[Tag]:
    cards = soup.select("li.desktop div.listView.holder.posS")
    if cards:
        return cards

    listing_heading = soup.find(["h2", "h3"], string=re.compile(r"Electric Scooters in India", re.I))
    if listing_heading:
        container = listing_heading.find_parent(["section", "div", "main"])
        if container:
            fallback_cards = []
            for item in container.find_all("li"):
                if item.find("h3") and item.find("a", href=True):
                    fallback_cards.append(item)
            if fallback_cards:
                return fallback_cards

    fallback_cards = []
    for item in soup.find_all("li"):
        title = item.find("h3")
        link = item.find("a", href=True)
        if title and link:
            fallback_cards.append(item)
    return fallback_cards


def parse_ev_cards(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    cards = get_listing_cards(soup)
    evs = []

    for card in cards:
        name_node = card.select_one("h3 a") or card.find("h3").find("a")
        if not name_node:
            continue

        name = clean_text(name_node.get_text())
        speed, range_value, extra_details = extract_specs(card)
        evs.append(
            {
                "name": name,
                "speed": speed,
                "range": range_value,
                "rating": extract_rating(card),
                "reviews": extract_reviews(card),
                "price": extract_price(card),
                "emi": extract_emi(card),
                "extra_details": extra_details,
            }
        )

    return evs


def get_deepseek_strategy() -> LLMExtractionStrategy:
    api_token = os.getenv(DEEPSEEK_API_KEY_ENV)
    if not api_token:
        raise RuntimeError(
            f"{DEEPSEEK_API_KEY_ENV} is missing. Add it to your .env file to enable DeepSeek extraction mode."
        )

    return LLMExtractionStrategy(
        provider=DEEPSEEK_PROVIDER,
        api_token=api_token,
        schema=EVScooter.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract each electric scooter listing into the schema fields: "
            "name, speed, range, rating, reviews, price, emi, and extra_details."
        ),
        input_format="html",
        verbose=False,
    )


def normalize_llm_rows(extracted_content: str) -> List[dict]:
    try:
        rows = json.loads(extracted_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("DeepSeek extraction returned invalid JSON.") from exc

    if not isinstance(rows, list):
        raise RuntimeError("DeepSeek extraction returned an unexpected payload.")

    normalized_rows = []
    for row in rows:
        if not isinstance(row, dict):
            continue

        normalized_rows.append(
            {
                "name": clean_text(str(row.get("name", "N/A"))),
                "speed": clean_text(str(row.get("speed", "N/A"))),
                "range": clean_text(str(row.get("range", "N/A"))),
                "rating": float(row.get("rating", 0) or 0),
                "reviews": int(row.get("reviews", 0) or 0),
                "price": clean_text(str(row.get("price", "N/A"))),
                "emi": clean_text(str(row.get("emi", "N/A"))),
                "extra_details": clean_text(str(row.get("extra_details", "N/A"))),
            }
        )

    return normalized_rows


async def fetch_page_result(crawler: AsyncWebCrawler, url: str, extraction_mode: str):
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="domcontentloaded",
        page_timeout=60000,
        delay_before_return_html=0.3,
        user_agent=USER_AGENT,
        verbose=False,
    )

    if extraction_mode == "deepseek":
        run_config.extraction_strategy = get_deepseek_strategy()

    result = await crawler.arun(url=url, config=run_config)
    if not result.success:
        raise RuntimeError(result.error_message or f"Failed to crawl {url}")

    return result


async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    required_keys: List[str],
    seen_names: Set[str],
    extraction_mode: str = "css",
    scraper_engine: str = "crawl4ai",
) -> Tuple[List[dict], bool]:
    """
    Fetches and processes a single page of EV scooter data using Crawl4AI for page loading.
    """
    if scraper_engine != "crawl4ai":
        raise RuntimeError(f"Unsupported scraper engine: {scraper_engine}")

    url = f"{base_url}?pageno={page_number}"
    print(f"Loading page {page_number}...")

    result = await fetch_page_result(crawler, url, extraction_mode)
    if extraction_mode == "deepseek":
        if not result.extracted_content:
            raise RuntimeError(f"DeepSeek extraction did not return content for page {page_number}.")
        extracted_data = normalize_llm_rows(result.extracted_content)
    else:
        html = result.cleaned_html or result.html
        extracted_data = parse_ev_cards(html)

    if not extracted_data:
        print(f"No EV scooters found on page {page_number}.")
        return [], True

    complete_evs = []
    for ev in extracted_data:
        if not all(key in ev for key in required_keys):
            continue

        if ev["name"] in seen_names:
            continue

        seen_names.add(ev["name"])
        complete_evs.append(ev)

    if not complete_evs:
        print(f"No new EV scooters found on page {page_number}.")
        return [], True

    print(f"Extracted {len(complete_evs)} EVs from page {page_number}.")
    return complete_evs, False
