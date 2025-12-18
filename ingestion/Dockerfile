FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install langchain langchain-community langchain-ollama

COPY ingest_papers.py .

EXPOSE 8000

# CMD ["python", "ingest_papers.py", "--query", "metformin diabetes AMPK", "--limit", "100", "--model ${LANGUAGE_MODEL}"]
CMD ["python", "ingest_papers.py", "--query", "metformin diabetes AMPK", "--limit", "100"]

