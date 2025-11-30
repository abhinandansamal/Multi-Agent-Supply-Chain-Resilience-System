import requests
from mcp.server.fastmcp import FastMCP
from src.utils.logger import setup_logger

logger = setup_logger("tool_currency")
mcp = FastMCP("Sentinell_Currency_Tool")

EXCHANGE_API_URL = "http://localhost:8001/v1/exchange_rate"

@mcp.tool()
def get_exchange_rate(currency_code: str) -> str:
    """
    Check the current exchange rate for a currency against USD.
    Use this when a user asks about costs in foreign currencies (e.g., 'What is the cost in TWD?').
    
    Args:
        currency_code (str): The 3-letter currency code (EUR, TWD, JPY, VND, GBP).
        
    Returns:
        str: The exchange rate (e.g., '1 USD = 31.5 TWD') or an error message.
    """
    logger.info(f"💱 Checking rate for: {currency_code}")
    
    try:
        response = requests.get(f"{EXCHANGE_API_URL}/{currency_code}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rate")
            return f"1 USD = {rate} {currency_code}"
        else:
            return f"Error: Currency '{currency_code}' not supported."
            
    except Exception as e:
        logger.error(f"Currency tool error: {e}")
        return f"Error connecting to currency service: {e}"

if __name__ == "__main__":
    # Test (Mock Supplier must be running!)
    print(get_exchange_rate("TWD"))