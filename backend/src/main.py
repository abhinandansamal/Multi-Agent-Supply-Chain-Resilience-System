import uvicorn
import datetime
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.utils.logger import setup_logger
from src.agents.watchtower import WatchtowerAgent
from src.api.models import ScanRequest, ScanResponse

# Initialize module-level logger
logger = setup_logger("api_server")

# Global State Container
# We use a dictionary or global variable to hold the agent instance 
# so it persists across requests but initializes only once.
agent_instance: Optional[WatchtowerAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the lifecycle of the FastAPI application.

    This context manager handles the initialization of heavy resources (like AI Agents)
    before the application starts serving requests, and cleans them up after shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Control is yielded back to the application to handle requests.
    """
    global agent_instance
    
    # --- Startup Phase ---
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} Backend v{settings.VERSION}...")
    
    try:
        logger.debug("Initializing Watchtower Agent (loading Vertex AI models)...")
        agent_instance = WatchtowerAgent()
        logger.info("✅ Watchtower Agent initialized successfully and ready for duty.")
    except Exception as e:
        logger.critical(f"❌ Critical Failure: Could not initialize Watchtower Agent. Error: {e}")
        # We re-raise to prevent the server from starting in a broken state
        raise e
    
    yield  # Application runs and handles requests here
    
    # --- Shutdown Phase ---
    logger.info("🛑 Shutting down Sentinell Backend...")
    # (Optional) Add cleanup logic here, e.g., closing DB connections if not handled by MCP
    agent_instance = None

# Create the FastAPI App with the Lifespan Manager
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API for Sentinell.ai - Autonomous Supply Chain Resilience System",
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing)
# Required to allow the Next.js Frontend (running on a different port) to talk to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains (e.g., ["https://sentinell.ai"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, str]:
    """
    Performs a lightweight health check of the API server.

    Returns:
        Dict[str, str]: A dictionary containing the status and current version.
    """
    return {"status": "healthy", "version": settings.VERSION}

@app.post("/api/scan", response_model=ScanResponse, tags=["Agents"])
async def trigger_scan(request: ScanRequest) -> ScanResponse:
    """
    Triggers a proactive risk scan for a specific region using the Watchtower Agent.

    This endpoint acts as the bridge between the User Interface and the AI logic.
    It accepts a region, runs the agentic loop, and returns a structured risk assessment.

    Args:
        request (ScanRequest): The input payload containing the target 'region'.

    Returns:
        ScanResponse: Structured object containing the risk level, summary, and timestamp.

    Raises:
        HTTPException(503): If the Agent is not yet initialized.
        HTTPException(500): If the Agent fails during execution.
    """
    global agent_instance
    
    # Fail fast if the agent failed to load during startup
    if not agent_instance:
        logger.error("Request received but Agent is not initialized.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="AI Agent is initializing or failed to start."
        )
    
    logger.info(f"📨 API Request received: Scanning region '{request.region}'")
    
    try:
        # Execute the Agent Logic (Blocking call for this demo)
        # In a production environment, this should be offloaded to a background task (Celery/Arq)
        report_text = agent_instance.scan_region(request.region)
        
        # Heuristic Risk Classification
        # We parse the LLM's text output to assign a structured "Badge" for the UI.
        risk_level = "LOW"
        upper_text = report_text.upper()
        
        if "CRITICAL" in upper_text or "HIGH RISK" in upper_text:
            risk_level = "CRITICAL"
        elif "MEDIUM" in upper_text:
            risk_level = "MEDIUM"
        elif "LOW" in upper_text or "NO RISK" in upper_text:
            risk_level = "LOW"
            
        logger.info(f"✅ Scan Complete. Determined Risk Level: {risk_level}")

        return ScanResponse(
            region=request.region,
            risk_level=risk_level,
            summary=report_text,
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error processing scan request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Agent execution failed: {str(e)}"
        )

if __name__ == "__main__":
    # Local Development Entry Point
    logger.info("Local development server starting...")
    # reload=True allows the server to auto-restart when you change code
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)