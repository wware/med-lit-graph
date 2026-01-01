FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY ingestion/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install langchain langchain-community langchain-ollama

# Copy ingestion code (maintaining structure)
COPY ingestion/*.py /app/
COPY ingestion/utils/ /app/utils/
COPY ingestion/pipelines/ /app/pipelines/

# Copy schema from repo root (no duplication needed!)
COPY schema/ /app/schema/

EXPOSE 8000

# Default command (can be overridden)
CMD ["python3", "ingest_papers.py", "--query", "metformin diabetes AMPK", "--limit", "100"]
