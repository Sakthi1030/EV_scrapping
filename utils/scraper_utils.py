import asyncio
import re
from typing import List, Set, Tuple

import requests
from bs4 import BeautifulSoup, Tag

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 30


def clean_text(value: str) -> str:
    return " ".join(value.split())


def extract_reviews(card: Tag) -> int:
    reviews_link = card.select_one(".startRating .bottomText a")
    if not reviews_link:
        return 0

    match = re.search(r"(\d+)", reviews_link.get_text(" ", strip=True))
    return int(match.group(1)) if match else 0


def extract_rating(card: Tag) -> float:
    rating_node = card.select_one(".ratingStarNew")
    if not rating_node:
        return 0.0

    try:
        return float(clean_text(rating_node.get_text()))
    except ValueError:
        return 0.0


def extract_specs(card: Tag) -> Tuple[str, str, str]:
    spec_nodes = card.select(".dotlist span")
    specs = [clean_text(node.get_text()) for node in spec_nodes if clean_text(node.get_text())]

    speed = specs[0] if len(specs) > 0 else "N/A"
    range_value = specs[1] if len(specs) > 1 else "N/A"
    extra_details = ", ".join(specs[2:]) if len(specs) > 2 else "N/A"
    return speed, range_value, extra_details


def extract_price(card: Tag) -> str:
    price_node = card.select_one(".price")
    if not price_node:
        return "N/A"

    return clean_text(price_node.get_text(" ", strip=True))


def extract_emi(card: Tag) -> str:
    emi_node = card.select_one(".emiStart")
    if not emi_node:
        return "N/A"

    return clean_text(emi_node.get_text(" ", strip=True))


def parse_ev_cards(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    cards = soup.select("li.desktop div.listView.holder.posS")
    evs = []

    for card in cards:
        name_node = card.select_one("h3 a.title")
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


async def fetch_page_html(url: str) -> str:
    def _fetch() -> str:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.text

    return await asyncio.to_thread(_fetch)


async def fetch_and_process_page(
    page_number: int,
    base_url: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    """
    Fetches and processes a single page of EV scooter data without using an LLM.
    """
    url = f"{base_url}?pageno={page_number}"
    print(f"Loading page {page_number}...")

    html = await fetch_page_html(url)
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
