FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        wget \
        curl \
        && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

WORKDIR /app
COPY . .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["python", "pmc_ner_pipeline.py"]
