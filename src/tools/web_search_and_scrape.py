import httpx
import json
from config.loader import load_config
from tools.base_tool import BaseTool
from tools.truncate_with_label import truncate_with_label


class WebSearchTool(BaseTool):
    def _write_log(self, **kwargs):
        tool_call_id = kwargs.get("tool_call_id", "")

        if not tool_call_id:
            return None

        config = load_config()
        result = kwargs.get("data", None)

        abs_path = f"{config.temp_path}/{tool_call_id}.out"
        with open(abs_path, "w") as f:
            f.write(json.dumps({"result": "No results." if result is None else result}))

        return abs_path

    def _truncate(self, call_id: str, **kwargs):
        if not call_id:
            return {
                "truncated": None,
                "full": {"result": kwargs.get("result", "No results.")},
            }

        config = load_config()
        result = kwargs.get("result", "No results")

        truncated_results = truncate_with_label(
            result, max_length=config.max_tool_call_output_length
        )

        return {"truncated": {"result": truncated_results}, "full": {"result": result}}

    def invoke(self, **kwargs):
        """Performs a web search given a query. Provide a search results limit. Default limit is 10 results.

        Returns:
            - markdown string respresentation of all the search results with each result formatted with TITLE, DESCRIPTION and URL.
        """

        query = kwargs.get("query", "")
        limit = int(kwargs.get("limit", 10))
        tool_call_id = kwargs.get("tool_call_id", "")

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
            result = response_json.get("data", "No results.")

            truncate_result = self._truncate(call_id=tool_call_id, result=result)

            truncated = truncate_result["truncated"]
            full_result = truncate_result["full"]

            log_path = self._write_log(
                tool_call_id=tool_call_id, result=full_result["result"]
            )

            return {"status": "ok", **truncated, "full_output_log": log_path}
        except Exception as e:
            return {
                "status": "error",
                "result": f"Error occurred trying to scrape: {e}.",
            }


class WebpageScrapeTool(BaseTool):
    pass


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
