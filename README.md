# EV Scooter Scraper

This project scrapes electric scooter listings from BikeDekho and saves the results to a CSV file.

It currently collects:

- scooter name
- top speed
- range
- rating
- review count
- price
- EMI text
- extra spec details shown in the listing card

## How It Works

The scraper requests the paginated BikeDekho listing pages and parses the scooter cards directly from the HTML using `BeautifulSoup`.

The current flow is:

1. Load page 1 from the BikeDekho electric scooters listing
2. Extract all scooter cards from the page
3. Move through pagination using `?pageno=...`
4. Stop when a page has no scooter cards
5. Save the combined results to `ev_scooters.csv`

## Project Structure

- `main.py`: entrypoint and crawl loop
- `config.py`: base URL and required output keys
- `utils/scraper_utils.py`: HTML fetching and extraction logic
- `utils/data_utils.py`: CSV writing helpers
- `models/ev_scooter.py`: data model for output fields
- `ev_scooters.csv`: latest scraped output

## Requirements

Install the dependencies:

```bash
pip install requests beautifulsoup4 lxml python-dotenv pydantic
```

## Run

```bash
python main.py
```

After the run completes, the scraped data will be written to:

```bash
ev_scooters.csv
```

## Output Columns

The CSV contains:

- `name`
- `speed`
- `range`
- `rating`
- `reviews`
- `price`
- `emi`
- `extra_details`

## Notes

- The scraper currently works without Groq or any LLM dependency.
- The site pagination uses `pageno`, not `page`.
- Because the site can change over time, selectors may need to be updated later if BikeDekho changes its listing layout.
