"""Web Search skill for real-time live information lookup."""

import time
import logging
from typing import Dict, Any, List
from datetime import datetime
import httpx
from app.skills.base import BaseSkill, SkillResult

logger = logging.getLogger("lara.skills.web_search")


class WebSearchSkill(BaseSkill):
    """Searches the live web for factual information with real-time fallbacks."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for real-time information, latest news, live weather, dates, or facts."

    @property
    def trigger_examples(self) -> List[str]:
        return [
            "search the web for latest Python release",
            "what is the date and time today",
            "look up today's weather in New York",
            "find documentation on FastAPI websockets",
            "search for latest AI news"
        ]

    async def execute(self, params: Dict[str, Any], user_id: str = "default_user") -> SkillResult:
        start_time = time.perf_counter()
        query = params.get("query", "").strip()
        if not query:
            return SkillResult(
                success=False,
                output="No search query provided.",
                error="empty_query",
                execution_time_ms=0.0
            )

        lower_q = query.lower()

        # Real-time Date / Time query check
        if any(w in lower_q for w in ["today's date", "current date", "what date is it", "current time", "what time is it"]):
            now = datetime.now()
            output = f"**Current Real-Time Date & Time:**\n- **Date:** {now.strftime('%A, %B %d, %Y')}\n- **Time:** {now.strftime('%I:%M:%S %p')} (Local Host Time)\n- **UTC:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            latency = (time.perf_counter() - start_time) * 1000.0
            return SkillResult(
                success=True,
                output=output,
                execution_time_ms=round(latency, 2)
            )

        # DuckDuckGo query
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get("https://api.duckduckgo.com/", params={
                    "q": query, "format": "json", "no_html": "1", "skip_disambig": "1",
                })
                if res.status_code == 200:
                    data = res.json()
                    abstract = data.get("AbstractText", "")
                    heading = data.get("Heading", "")
                    related_topics = [
                        t.get("Text") for t in data.get("RelatedTopics", []) if isinstance(t, dict) and "Text" in t
                    ][:3]

                    if abstract:
                        output = f"**{heading}**\n{abstract}"
                        if related_topics:
                            output += "\n\n*Related details:*\n- " + "\n- ".join(related_topics)
                        latency = (time.perf_counter() - start_time) * 1000.0
                        return SkillResult(
                            success=True,
                            output=output,
                            execution_time_ms=round(latency, 2)
                        )
                    elif related_topics:
                        output = f"Search results for **'{query}'**:\n- " + "\n- ".join(related_topics)
                        latency = (time.perf_counter() - start_time) * 1000.0
                        return SkillResult(
                            success=True,
                            output=output,
                            execution_time_ms=round(latency, 2)
                        )
        except Exception as e:
            logger.warning("Web search error: %s", e)

        # Fallback live response
        latency = (time.perf_counter() - start_time) * 1000.0
        return SkillResult(
            success=False,
            output=f"No search results available for '{query}'. The search provider may be unavailable or have no matching instant answer.",
            error="search_unavailable",
            execution_time_ms=round(latency, 2)
        )
