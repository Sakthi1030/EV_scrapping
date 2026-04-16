# EV Scooter Scraper

This project scrapes electric scooter listings from BikeDekho and saves the results to a CSV file.

The goal of the project is to collect structured EV scooter data such as price, speed, range, rating, reviews, EMI, and extra listing details in an automated way.

## Why This Project

This scraper was built to turn semi-structured website listings into a reusable dataset for:

- market research
- price comparison
- EV product analysis
- portfolio and resume demonstration
- future data pipelines or dashboards

## Tech Stack

The project uses a hybrid approach:

- `crawl4ai` for page loading, crawling, and rendered page retrieval
- `BeautifulSoup` for deterministic HTML parsing
- optional `DeepSeek` integration through `crawl4ai` for schema-based LLM extraction
- `pydantic` for the output data model
- `csv` for exporting results

## Why Use `crawl4ai`

Using only `BeautifulSoup` works well when the HTML is already available and stable, but `crawl4ai` adds advantages:

- it handles browser-style crawling more cleanly for pages that may be dynamic
- it gives a consistent crawling layer for pagination and rendered content
- it allows the same project to support both rule-based extraction and LLM-based extraction
- it makes the scraper easier to extend later for more complex pages

In this project, `crawl4ai` is used as the main crawling engine, while `BeautifulSoup` handles the reliable extraction logic.

## Why Add `DeepSeek`

`DeepSeek` is integrated as an optional extraction backend through `crawl4ai`.

Its advantage is that it can help when:

- page structures are messy or inconsistent
- fixed selectors become hard to maintain
- you want schema-based extraction with less manual parsing
- you want to quickly prototype extraction for new websites

For this BikeDekho page, the CSS/HTML parsing path is still the default because it is faster, cheaper, and more stable for the current listing structure. But `DeepSeek` is integrated so the project can support an LLM extraction workflow too.

## Why Not Use Only `BeautifulSoup`

Using only `BeautifulSoup` is simple and efficient, but it has limits:

- it depends fully on stable HTML structure
- it can struggle when pages are rendered dynamically
- it does not provide an easy built-in path for schema-based LLM extraction

That is why this project uses `crawl4ai + BeautifulSoup` together:

- `crawl4ai` handles the crawling layer
- `BeautifulSoup` handles precise extraction
- `DeepSeek` remains available as an optional intelligent extraction layer

## What It Collects

The scraper collects:

- scooter name
- top speed
- range
- rating
- review count
- price
- EMI text
- extra spec details shown in the listing card

## How It Works

The current flow is:

1. Start the crawler with `crawl4ai`
2. Load BikeDekho electric scooter listing pages using `?pageno=...`
3. Parse the cleaned HTML with `BeautifulSoup`
4. Extract each scooter card into a structured format
5. Remove duplicates across pages
6. Save the final records to `ev_scooters.csv`

The scraper currently extracts around 295 listings from the live site.

## Extraction Modes

The project supports two extraction modes:

1. `css`
   This is the default and recommended mode. It uses `crawl4ai` for crawling and `BeautifulSoup` for parsing.
2. `deepseek`
   This uses `crawl4ai` with an LLM extraction strategy powered by `DeepSeek`.

For the current website, `css` mode gives the most reliable output.

## Project Structure

- `main.py`: entrypoint and crawl loop
- `config.py`: base URL, extraction mode, and runtime settings
- `utils/scraper_utils.py`: Crawl4AI page loading, BeautifulSoup parsing, and optional DeepSeek extraction
- `utils/data_utils.py`: CSV writing helpers
- `models/ev_scooter.py`: data model for output fields
- `ev_scooters.csv`: latest scraped output

## Requirements

Install the dependencies:

```bash
pip install crawl4ai beautifulsoup4 lxml python-dotenv pydantic requests
```

## Run

```bash
python main.py
```

After the run completes, the scraped data will be written to:

```bash
ev_scooters.csv
```

## Optional DeepSeek Mode

If you want to enable LLM-based extraction through `crawl4ai`, add this to your `.env`:

```env
DEEPSEEK_API_KEY=your_key_here
```

Then switch the extraction mode in `config.py`:

```python
EXTRACTION_MODE = "deepseek"
```

For the current BikeDekho listing page, the default `css` mode is the recommended option because it gives the same result shape without depending on an external model.

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

- `DeepSeek` is integrated as an optional extraction backend.
- The site pagination uses `pageno`, not `page`.
- Because the site can change over time, selectors may need to be updated later if BikeDekho changes its listing layout.
