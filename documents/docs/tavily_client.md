## `class TavilyClient`

A client for interacting with the Tavily Search API.

This client provides a simple interface for performing web searches using the
Tavily API.

### `def __init__`

Initializes the TavilyClient.

Args:
    api_key: The Tavily API key. If not provided, it will be read from
        the TAVILY_API_KEY environment variable.

Raises:
    ValueError: If the API key is not provided.

### `def search`

Performs a search using the Tavily API.

Args:
    query: The search query.
    max_results: The maximum number of results to return.

Returns:
    A list of search results, or an empty list if the search fails.

