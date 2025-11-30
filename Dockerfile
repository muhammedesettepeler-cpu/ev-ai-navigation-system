FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY backend/ ./backend/
COPY data/ ./data/
COPY .env .
COPY embeddings_integration.py .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Run the orchestrator
CMD ["python", "backend/orchestrator.py"]