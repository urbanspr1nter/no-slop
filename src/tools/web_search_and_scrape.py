import httpx
from config.loader import load_config


def web_search(query: str, limit: int = 10) -> str:
    """Performs a web search given a query. Provide a search results limit. Default limit is 10 results.

    Returns:
        - markdown string respresentation of all the search results with each result formatted with TITLE, DESCRIPTION and URL.
    """

    payload = {"query": query, "limit": limit}

    config = load_config()

    if not config.search_and_scrape_service_url:
        return {
            "status": "error",
            "result": "Must provide search and scrape URL in config.",
        }

    try:
        response = httpx.post(
            f"{config.search_and_scrape_service_url}/search",
            json=payload,
            timeout=httpx.Timeout(120.0),
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "result": f"Could not make a search request for query: {query}.",
            }

        response_json = response.json()

        return {"status": "ok", "result": response_json.get("data", "No results.")}
    except Exception as e:
        return {"status": "error", "result": f"Error occurred trying to scrape: {e}."}


def web_page_scrape(url: str) -> str:
    """Scrapes a web page for contents given a URL. Returns the markdown representation of the web page.

    Returns:
        - markdown string representation of the web page.
    """

    if not len(url):
        return {"status": "error", "result": "Provide a url to scrape contents for."}

    payload = {"url": url}

    config = load_config()
    if not config.search_and_scrape_service_url:
        return {
            "status": "error",
            "result": "Must provide search and scrape URL in config.",
        }

    try:
        response = httpx.post(
            f"{config.search_and_scrape_service_url}/scrape",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=httpx.Timeout(120.0),
        )

        if response.status_code != 200:
            return {
                "status": "error",
                "result": f"Could not scrape the web page for URL: {url}.",
            }

        response_json = response.json()

        return {"status": "ok", "result": response_json.get("data", "No content.")}
    except Exception as e:
        return {"status": "error", "result": f"Error occurred trying to scrape: {e}."}
