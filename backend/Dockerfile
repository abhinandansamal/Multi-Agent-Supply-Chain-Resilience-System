# Use an official lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# 1. Install System Dependencies
# gcc is often needed for installing Python libraries
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 2. Copy Requirements first (Layer Caching optimization)
# This makes future builds faster if you only change code, not libraries
COPY requirements.txt .

# 3. Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the entire source code
COPY . .

# 5. Set Environment Variables
# PORT is required by Google Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# 6. Define the Start Command
# We use the module syntax (-m) just like we did locally
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]