FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ingestion/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy code preserving package structure
COPY ingestion /app/ingestion
COPY schema /app/schema

# Install schema package
WORKDIR /app/schema
RUN pip install -e .
WORKDIR /app

# Set python path to allow absolute imports
ENV PYTHONPATH=/app

EXPOSE 8000

# Default command (can be overridden)
CMD ["python3", "-m", "ingestion.ingest_papers", "--query", "metformin diabetes AMPK", "--limit", "100"]
