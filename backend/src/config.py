import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class Settings(BaseSettings):
    """
    Application Settings configuration.
    
    Inherits from Pydantic BaseSettings to automatically load environment 
    variables from the .env file or system environment.
    """
    
    # Project Metadata
    PROJECT_NAME: str = "Sentinell.ai"
    VERSION: str = "1.0.0"
    
    # Google Cloud & AI Configuration
    GOOGLE_CLOUD_PROJECT: str 
    GOOGLE_CLOUD_REGION: str
    
    # Model Configuration
    MODEL_NAME: str = "gemini-2.5-flash-lite" 
    
    # Infrastructure
    LOG_LEVEL: str = "INFO"
    
    # Database Configuration
    @property
    def DATABASE_PATH(self) -> str:
        """Returns the absolute path to the SQLite database file."""
        current_file = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(current_file) 
        return os.path.join(base_dir, "../data/supply_chain.db")

    class Config:
        """Pydantic config to read from .env file."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore" 

@lru_cache()
def get_settings() -> Settings:
    """
    Creates and returns a cached instance of the Settings class.
    
    Using lru_cache ensures we only read the .env file once per execution,
    improving performance.
    
    Returns:
        Settings: The application settings object.
    """
    try:
        return Settings()
    except Exception as e:
        logger.critical(f"❌ Configuration Error: Missing required .env variables! {e}")
        raise

settings = get_settings()