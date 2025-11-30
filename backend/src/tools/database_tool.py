import sqlite3
import os
from mcp.server.fastmcp import FastMCP
from src.config import settings
from src.utils.logger import setup_logger

# Initialize structured logging
logger = setup_logger("tool_database")

# Initialize the MCP Server
# This name helps identify the tool source in complex multi-agent systems
mcp = FastMCP("Sentinell_Inventory_Data")

def get_db_connection() -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database defined in settings.
    
    Returns:
        sqlite3.Connection: Active database connection object.
    
    Raises:
        FileNotFoundError: If the database file does not exist.
        sqlite3.Error: If connection fails.
    """
    try:
        if not os.path.exists(settings.DATABASE_PATH):
            logger.critical(f"Database file missing at: {settings.DATABASE_PATH}")
            raise FileNotFoundError(f"Database not found at {settings.DATABASE_PATH}")
            
        conn = sqlite3.connect(settings.DATABASE_PATH)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

@mcp.tool()
def query_inventory_by_region(region: str) -> str:
    """
    Retrieves inventory levels for all parts sourced from a specific geographic region.
    
    Use this tool when analyzing supply chain risks associated with a location 
    (e.g., "Earthquake in Taiwan" -> check "Taiwan" inventory).

    Args:
        region (str): The region name (e.g., 'Taiwan', 'China', 'USA').

    Returns:
        str: A formatted report of inventory items, stock levels, and risk status.
    """
    logger.info(f"🔍 querying inventory for region: {region}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Join Inventory with Suppliers to filter by Supplier Region
        query = """
        SELECT i.part_name, i.stock_level, i.min_required, s.name, i.category
        FROM inventory i 
        JOIN suppliers s ON i.supplier_id = s.id 
        WHERE s.region LIKE ?
        """
        # Use LIKE with wildcards for flexible matching (e.g., "taiwan" matches "Taiwan")
        cursor.execute(query, (f"%{region}%",))
        results = cursor.fetchall()
        
        if not results:
            msg = f"No inventory records found linked to region: '{region}'."
            logger.info(msg)
            return msg
        
        # Format output for LLM readability
        response = [f"📦 **Inventory Exposure Report for {region}:**"]
        
        for row in results:
            part, stock, required, supplier, category = row
            
            # Risk Logic: Identify critical shortages
            if stock == 0:
                status = "🔴 STOCKOUT"
            elif stock < required:
                status = "Rx⚠️ LOW STOCK"
            else:
                status = "✅ OK"
                
            response.append(
                f"- **{part}** ({category}): Stock {stock}/{required} [{status}] via {supplier}"
            )
            
        return "\n".join(response)

    except sqlite3.Error as e:
        logger.error(f"SQL Error during region query: {e}")
        return f"Error querying database: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def check_supplier_reliability(supplier_name: str) -> str:
    """
    Retrieves the reliability score for a specific supplier.

    Args:
        supplier_name (str): The name of the supplier to check.

    Returns:
        str: The reliability score (0.0 - 1.0) and location.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT reliability_score, region FROM suppliers WHERE name LIKE ?", 
            (f"%{supplier_name}%",)
        )
        result = cursor.fetchone()
        
        if result:
            score, loc = result
            return f"Supplier '{supplier_name}' ({loc}) has a reliability score of: {score:.2f}"
        
        return f"Supplier '{supplier_name}' not found in the database."
    finally:
        conn.close()

if __name__ == "__main__":
    # Internal Unit Test
    print("🧪 Running Database Tool Test...")
    try:
        print(query_inventory_by_region("Taiwan"))
        print(check_supplier_reliability("TSMC_Logic"))
        print("✅ Database Tool Tests Passed.")
    except Exception as e:
        print(f"❌ Tests Failed: {e}")