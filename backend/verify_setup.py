import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
region = os.getenv("GOOGLE_CLOUD_REGION")

print(f"🔍 Testing connection for Project: [{project_id}] in Region: [{region}]")

try:
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=region)

    # Test: Try to load the Gemini Model
    model = GenerativeModel("gemini-2.5-flash-lite")
    response = model.generate_content("Hello! Are you ready for the supply chain project?")

    print("\n✅ SUCCESS! Google Cloud is connected.")
    print(f"🤖 Model Replied: {response.text}")

except Exception as e:
    print("\n❌ ERROR: Something is wrong with the setup.")
    print(e)