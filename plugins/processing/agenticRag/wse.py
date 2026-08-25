"""Web Search Engine (WSE): Real-time web querying via Tavily API."""

from tavily import AsyncTavilyClient
from app.helps.utils import logger
from settings.config import params


class ErrorMessage:
    silent_bug = ""
    search_failed = "[WEB SEARCH STATUS: Internet search failed, answer using general knowledge.]"


class WebSearchEngine(ErrorMessage):
    """Asynchronous internet search engine powered by Tavily."""

    def __init__(self):
        self.client = AsyncTavilyClient(api_key=params.TAVILY_TOKEN)
        self.tavily_topic = params.TAVILY_TOPIC
        self.tavily_depth = params.TAVILY_DEPTH
        self.tavily_max_text_length = params.TAVILY_MAX_TEXT_LENGTH
        self.tavily_min_query_length = params.TAVILY_MIN_QUERY_LENGTH
        self.tavily_max_search_results = params.TAVILY_MAX_SEARCH_RESULTS
        self.tavily_include_answer = params.TAVILY_INCLUDE_ANSWER
        self.tavily_include_domains = params.TAVILY_INCLUDE_DOMAINS
        self.tavily_exclude_domains = params.TAVILY_EXCLUDE_DOMAINS
        self.tavily_include_raw_content = params.TAVILY_INCLUDE_RAW_CONTENT
        self.tavily_time_range = params.TAVILY_TIME_RANGE
        self.tavily_relevance_score = params.TAVILY_RELEVANCE_SCORE

    async def search(self, query: str) -> str:
        """Perform search query and format result snippet for LLM context."""
        if not query or not isinstance(query, str):
            return ErrorMessage.silent_bug

        bot_name = [params.NAME.lower()]
        query = " ".join(word for word in query.strip().split() if word.lower() not in bot_name).strip()
        if len(query) > 400:
            return ErrorMessage.silent_bug

        try:
            data = await self.client.search(
                query=query,
                topic=self.tavily_topic[0],
                search_depth=self.tavily_depth[0],
                time_range=self.tavily_time_range[0],
                include_answer=self.tavily_include_answer[1],
                max_results=self.tavily_max_search_results,
                include_raw_content=self.tavily_include_raw_content,
                include_domains=self.tavily_include_domains,
                exclude_domains=self.tavily_exclude_domains,
            )

            return self._format_results(data)

        except Exception as err:
            logger.error(f"[ERROR WSE] Web search failed: {err}", exc_info=True)
            return ErrorMessage.search_failed

    def _format_results(self, data: dict) -> str:
        """Format raw search payload into structured text block."""
        if not data or not isinstance(data, dict):
            return ErrorMessage.silent_bug

        prompt_context = []

        # Tavily AI summary
        tavily_answer = data.get("answer", "").strip()
        if tavily_answer:
            prompt_context.append(f"* Summary=> {tavily_answer}")

        # List of web sources
        search_results = data.get("results", [])
        if not search_results:
            return ErrorMessage.silent_bug

        formatted_sources = []
        for index, source in enumerate(search_results[: self.tavily_max_search_results], start=1):
            relevance_score = source.get("score", 0)
            if relevance_score < self.tavily_relevance_score[6]:
                continue

            page_title = source.get("title", "Untitled").strip()
            page_content = source.get("content", "").strip()

            if len(page_content) > self.tavily_max_text_length:
                page_content = page_content[: self.tavily_max_text_length] + "..."

            if page_content:
                formatted_sources.append(f"[{index}] {page_title}\n    {page_content}\n")

        if formatted_sources:
            prompt_context.append("* Details=>\n" + "\n".join(formatted_sources))

        if not prompt_context:
            return ErrorMessage.silent_bug

        return "\n".join(prompt_context)
