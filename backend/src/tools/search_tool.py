from mcp.server.fastmcp import FastMCP
from src.utils.logger import setup_logger

logger = setup_logger("tool_search")
mcp = FastMCP("Sentinell_Search")

# ---------------------------------------------------------
# SIMULATED NEWS FEED (The "Golden Dataset" for Demo)
# This ensures that when we present the project, the agent 
# ALWAYS finds the risk you want to show.
# ---------------------------------------------------------
MOCK_NEWS_DATABASE = {
    "taiwan": [
        "BREAKING: Magnitude 7.4 Earthquake strikes off east coast of Taiwan.",
        "Taiwan Semiconductor Manufacturing Co (TSMC) evacuates factory areas due to safety protocols.",
        "Global supply chain analysts predict 2-week delays in semiconductor shipments."
    ],
    "vietnam": [
        "Vietnam Port Authority reports normal operations despite heavy rains.",
        "Tech manufacturing exports from Hanoi see 5% growth this quarter."
    ],
    "usa": [
        "West Coast Port Strike: Logistics stalled in California.",
        "Shipping delays expected for domestic electronics components.",
        "US Logistics union announces 48-hour walkout."
    ],
    "logistics": [
        "Global container shipping rates stabilize after last month's spike.",
        "Air freight capacity increases on trans-pacific routes."
    ]
}

@mcp.tool()
def search_news(query: str) -> str:
    """
    Searches for recent news headlines and current events.
    Useful for monitoring external risks like weather, geopolitics, or strikes.
    
    Args:
        query (str): The search keywords (e.g., "Taiwan earthquake", "Port strike LA").
    """
    logger.info(f"🔎 Agent is searching news for: '{query}'")
    
    query_lower = query.lower()
    results = []

    # 1. Check our "Demo Scenarios" first
    # We check if any key from our database exists in the query
    found_key = False
    for key, articles in MOCK_NEWS_DATABASE.items():
        if key in query_lower:
            results.extend(articles)
            found_key = True
    
    # 2. Format the output
    if results:
        formatted_news = f"📰 **News Results for '{query}':**\n"
        for i, news in enumerate(results, 1):
            formatted_news += f"{i}. {news}\n"
        
        logger.info(f"Found {len(results)} articles for query.")
        return formatted_news

    # 3. Fallback for unknown queries
    logger.warning(f"No mock news found for: {query}")
    return f"No recent breaking news found regarding '{query}'."

if __name__ == "__main__":
    # Test the tool
    print("🧪 Testing Search Tool...")
    print(search_news("USA"))