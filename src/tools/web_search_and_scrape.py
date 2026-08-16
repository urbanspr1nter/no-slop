import json

import httpx

from config.loader import load_config
from tools.base_tool import BaseTool
from tools.helpers import err, ok
from tools.truncate_with_label import truncate_with_label

_SEARCH_OR_SCRAPE_TIMEOUT = httpx.Timeout(120.0)


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Performs a web search given a query. Optionally, provide a search results "
        "limit. Default limit is 10 results. Returns a markdown string representation "
        "of all the search results with each result formatted with TITLE, DESCRIPTION "
        "and URL."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Query to search the web for related content.",
            },
            "limit": {
                "type": "number",
                "description": "Number of results to return. Default is 10.",
            },
        },
        "required": ["query"],
    }

    def _truncate(self, result: str, tool_call_id: str) -> dict:
        """Truncate a long result for the model, keeping the full text for logging."""
        config = load_config()

        if not tool_call_id:
            return {"truncated": None, "full": result}

        truncated = truncate_with_label(
            result, max_length=config.max_tool_call_output_length
        )
        return {"truncated": truncated, "full": result}

    def _write_log(self, result, tool_call_id: str, config) -> str | None:
        if not tool_call_id:
            return None

        abs_path = f"{config.temp_path}/{tool_call_id}.out"
        with open(abs_path, "w") as f:
            f.write(json.dumps({"result": "No results." if result is None else result}))

        return abs_path

    def invoke(self, **kwargs) -> dict:
        query = kwargs.get("query", "")
        try:
            limit = int(kwargs.get("limit", 10))
        except (TypeError, ValueError):
            return err("Provide a valid integer for the search results limit.")

        tool_call_id = kwargs.get("tool_call_id", "")

        config = load_config()
        if not config.search_and_scrape_service_url:
            return err("Must provide search and scrape URL in config.")

        try:
            response = httpx.post(
                f"{config.search_and_scrape_service_url}/search",
                json={"query": query, "limit": limit},
                timeout=_SEARCH_OR_SCRAPE_TIMEOUT,
            )
        except Exception as e:
            return err(f"Error occurred trying to search: {e}.")

        if response.status_code != 200:
            return err(f"Could not make a search request for query: {query}.")

        result = response.json().get("data", "No results.")

        truncate_result = self._truncate(result=result, tool_call_id=tool_call_id)
        truncated = truncate_result["truncated"]
        full = truncate_result["full"]

        log_path = self._write_log(result=full, tool_call_id=tool_call_id, config=config)

        return ok(
            {
                "result": truncated if truncated is not None else full,
                "full_output_log": log_path,
            }
        )


class WebPageScrapeTool(BaseTool):
    name = "web_page_scrape"
    description = (
        "Scrapes a web page for contents given a URL. Returns the markdown "
        "representation of the web page."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Web page URL to scrape contents.",
            }
        },
        "required": ["url"],
    }

    def invoke(self, **kwargs) -> dict:
        url = kwargs.get("url", "")

        if not url:
            return err("Provide a url to scrape contents for.")

        config = load_config()
        if not config.search_and_scrape_service_url:
            return err("Must provide search and scrape URL in config.")

        try:
            response = httpx.post(
                f"{config.search_and_scrape_service_url}/scrape",
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=_SEARCH_OR_SCRAPE_TIMEOUT,
            )
        except Exception as e:
            return err(f"Error occurred trying to scrape: {e}.")

        if response.status_code != 200:
            return err(f"Could not scrape the web page for URL: {url}.")

        return ok(response.json().get("data", "No content."))
