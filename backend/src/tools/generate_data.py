import sqlite3
import os
import sys

# Add project root to Python path to ensure imports work when running as a script
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import settings
from src.utils.logger import setup_logger

# Initialize a specific logger for data generation
logger = setup_logger("data_seeder")

def setup_db() -> None:
    """
    Initializes the SQLite database with the specific schema and synthetic data 
    required for the Sentinell.ai demo scenarios.
    
    Actions:
    1. Creates the directory structure if missing.
    2. Drops existing tables (clean slate).
    3. Creates 'suppliers' and 'inventory' tables.
    4. Seeds data designed to demonstrate specific supply chain risks:
       - Critical dependency on Taiwan (Logic-Core-CPUs).
       - Backup suppliers in Vietnam (with lower reliability).
    """
    db_path = settings.DATABASE_PATH
    
    logger.info(f"⚙️  Starting Database Initialization at: {db_path}")
    
    # 1. Ensure the directory exists
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    except OSError as e:
        logger.critical(f"Failed to create directory for database: {e}")
        raise

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 2. Clean Slate (Drop old tables to avoid conflicts during development)
        cursor.execute('DROP TABLE IF EXISTS inventory')
        cursor.execute('DROP TABLE IF EXISTS suppliers')

        # 3. Create Tables
        # Suppliers: Represents external entities we buy from
        cursor.execute('''
        CREATE TABLE suppliers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            reliability_score FLOAT
        )
        ''')
        
        # Inventory: Represents internal stock levels
        cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            part_name TEXT NOT NULL,
            supplier_id INTEGER,
            stock_level INTEGER,
            price FLOAT,
            min_required INTEGER,
            category TEXT,
            FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
        )
        ''')

        # 4. Add Seed Data
        
        # SCENARIO SETUP:
        # We need a mix of regions to demonstrate the "Search -> Filter" capability.
        # TSMC (Taiwan) is high quality (0.98) but will be the target of our "Earthquake" event.
        # Hanoi (Vietnam) is the backup, but has lower reliability (0.70).
        
        suppliers = [
            (1, "TSMC_Logic", "Taiwan", 0.98),
            (2, "Shenzhen_Electronics", "China", 0.85),
            (3, "Hanoi_Components", "Vietnam", 0.70), 
            (4, "Texas_Instruments_Local", "USA", 0.99)
        ]
        cursor.executemany('INSERT INTO suppliers VALUES (?,?,?,?)', suppliers)

        inventory_data = []
        
        # A. Critical Risk Items (Source: Taiwan)
        # We intentionally set stock (150) below min_required (200) to trigger alerts.
        for i in range(1, 11):
            inventory_data.append((i, f"Logic-Core-CPU-X{i}", 1, 150, 450.00, 200, "Critical"))

        # B. Bulk Commodities (Source: China)
        # Healthy stock levels
        for i in range(11, 31):
            inventory_data.append((i, f"Resistor-5k-{i}", 2, 10000, 0.05, 5000, "Generic"))
            
        # C. Local Parts (Source: USA)
        # Healthy stock levels
        for i in range(31, 51):
            inventory_data.append((i, f"Connector-TypeC-{i}", 4, 2000, 1.50, 500, "Generic"))

        cursor.executemany('INSERT INTO inventory VALUES (?,?,?,?,?,?,?)', inventory_data)
        
        conn.commit()
        logger.info("✅ Database successfully seeded with 50 inventory items and 4 suppliers.")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error occurred: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_db()