FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install langchain langchain-community langchain-ollama

# Copy all Python files and directories, maintaining structure
COPY *.py /app/
COPY utils/ /app/utils/
COPY pipelines/ /app/pipelines/

# Also copy schema directory from parent (needed for imports)
COPY ../schema/ /app/schema/

EXPOSE 8000

# Default command (can be overridden)
CMD ["python3", "ingest_papers.py", "--query", "metformin diabetes AMPK", "--limit", "100"]
