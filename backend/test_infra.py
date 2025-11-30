from src.config import settings
from src.utils.logger import setup_logger
import os

# 1. Setup Logger
logger = setup_logger("infrastructure_test")

def run_test():
    print("------------------------------------------------")
    logger.info("🚀 Starting Infrastructure Test...")
    
    # 2. Test Configuration Loading
    logger.info(f"Checking Project: {settings.GOOGLE_CLOUD_PROJECT}")
    logger.info(f"Checking Region:  {settings.GOOGLE_CLOUD_REGION}")
    logger.info(f"Checking Model:   {settings.MODEL_NAME}")
    logger.info(f"DB Path Target:   {settings.DATABASE_PATH}")

    # 3. Verify Log File Creation
    # We go up two levels to find the logs folder
    log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "sentinell.log")
    
    if os.path.exists(log_file_path):
        logger.info(f"✅ Log file successfully created at: {log_file_path}")
    else:
        logger.error("❌ Log file NOT found!")

    print("------------------------------------------------")
    print("✅ If you see the project ID above, config is working.")
    print("✅ If you see this message, logger is working.")

if __name__ == "__main__":
    run_test()