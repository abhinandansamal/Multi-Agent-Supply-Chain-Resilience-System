import uvicorn
import random
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

# --- Configuration ---
# Percentage chance (0.0 to 1.0) that the supplier rejects the order.
# Used to test the resilience of the Procurement Agent.
FAILURE_RATE = 0.2 

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [MOCK_SUPPLIER] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- FastAPI App Definition ---
app = FastAPI(
    title="External Supplier Agent (Mock)",
    description="Simulates a vendor API (e.g., TSMC or DigiKey) that receives Purchase Orders via A2A protocol.",
    version="1.0.0"
)

# --- Data Models (Pydantic V2) ---

class PurchaseOrder(BaseModel):
    """
    Represents an incoming purchase request from a client agent.

    Attributes:
        part_name (str): The SKU or name of the component (e.g., 'Logic-Core-CPU').
        quantity (int): The number of units requested. Must be greater than 0.
        urgent (bool): Flag indicating if expedited shipping is required.
    """
    part_name: str = Field(..., description="The SKU or name of the component to purchase")
    quantity: int = Field(..., gt=0, description="Amount required (must be > 0)")
    urgent: bool = Field(False, description="If true, adds express shipping fees")

    # Modern Pydantic V2 configuration
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "part_name": "Logic-Core-CPU-X1",
                "quantity": 50,
                "urgent": True
            }
        }
    )

class OrderResponse(BaseModel):
    """
    Represents the formal response from the supplier.

    Attributes:
        order_id (str): A unique confirmation ID (or 'N/A' if rejected).
        status (str): The outcome of the request ('CONFIRMED' or 'REJECTED').
        total_cost (float): The final calculated price including shipping.
        message (str): A human-readable explanation of the status.
    """
    order_id: str
    status: str
    total_cost: float
    message: str

# Initialize App
app = FastAPI(
    title="External Supplier Agent (Mock)",
    description="Simulates a vendor API with OpenAPI standards.",
    version="1.0.0"
)

# --- Endpoints ---

@app.get("/health", tags=["System"])
def health_check():
    """
    Simple heartbeat endpoint to verify the mock server is running.
    """
    return {"status": "online", "vendor": "Global-Chips-Inc", "port": 8001}

@app.post("/v1/order", response_model=OrderResponse, tags=["Orders"])
def receive_order(order: PurchaseOrder) -> OrderResponse:
    """
    Processes an incoming Purchase Order.

    Simulates real-world business logic including:
    1. Dynamic pricing based on urgency.
    2. Randomized inventory failures (Stockouts) to test agent resilience.

    Args:
        order (PurchaseOrder): The validated order request.

    Returns:
        OrderResponse: The confirmation details or rejection reason.
    """
    logger.info(f"📦 Received order request: {order.quantity} x {order.part_name} (Urgent={order.urgent})")

    # 1. Simulation Logic: Random Stockout
    # We introduce artificial chaos to ensure our Procurement Agent handles rejection gracefully.
    if random.random() < FAILURE_RATE:
        logger.warning(f"❌ Order Rejected: Artificial stockout triggered for {order.part_name}")
        return OrderResponse(
            order_id="N/A",
            status="REJECTED",
            total_cost=0.0,
            message=f"We are currently out of stock for {order.part_name}."
        )

    # 2. Simulation Logic: Pricing Calculation
    base_price = 50.0  # Mock base price per unit
    shipping_fee = 500.0 if order.urgent else 100.0
    
    total_cost = (order.quantity * base_price) + shipping_fee
    
    # Generate a fake PO number
    order_id = f"PO-{random.randint(10000, 99999)}"
    
    logger.info(f"✅ Order Accepted: {order_id} | Total: ${total_cost}")
    
    return OrderResponse(
        order_id=order_id,
        status="CONFIRMED",
        total_cost=total_cost,
        message=f"Order confirmed. Estimated delivery: {'1 day' if order.urgent else '3 days'}."
    )

# --- Currency Conversion Endpoint (OpenAPI Tool Target) ---
@app.get("/v1/exchange_rate/{currency}", tags=["Currency"])
def get_exchange_rate(currency: str):
    """
    Returns the exchange rate of a currency against USD.
    Supported: EUR, TWD, JPY, VND.
    """
    # Mock Database of Rates
    # In a real app, this would query a live Forex service.
    rates = {
        "EUR": 0.92,  # 1 USD = 0.92 EUR
        "TWD": 31.5,  # 1 USD = 31.5 TWD
        "JPY": 150.0, # 1 USD = 150 JPY
        "VND": 24500.0, # 1 USD = 24,500 VND
        "GBP": 0.79   # 1 USD = 0.79 GBP
    }
    
    rate = rates.get(currency.upper())
    if not rate:
        raise HTTPException(status_code=404, detail="Currency not supported")
    
    return {
        "base": "USD",
        "target": currency.upper(),
        "rate": rate,
        "timestamp": "2025-11-30T12:00:00Z"
    }

if __name__ == "__main__":
    # IMPORTANT: We run this on port 8001 to avoid conflict with the main application (8000)
    logger.info("🌍 External Supplier Agent starting on Port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)