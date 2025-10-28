import os
from tavily import TavilyClient as Tavily
from loguru import logger

class TavilyClient:
    """
    A client for interacting with the Tavily Search API.

    This client provides a simple interface for performing web searches using the
    Tavily API.
    """

    def __init__(self, api_key: str = None):
        """
        Initializes the TavilyClient.

        Args:
            api_key: The Tavily API key. If not provided, it will be read from
                the TAVILY_API_KEY environment variable.

        Raises:
            ValueError: If the API key is not provided.
        """
        api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Tavily API key not provided. Set the TAVILY_API_KEY environment variable.")
        self.client = Tavily(api_key=api_key)

    def search(self, query: str, max_results: int = 5) -> list:
        """
        Performs a search using the Tavily API.

        Args:
            query: The search query.
            max_results: The maximum number of results to return.

        Returns:
            A list of search results, or an empty list if the search fails.
        """
        logger.debug(f"Performing Tavily search for: '{query}'")
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=max_results)
            return response['results']
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []
