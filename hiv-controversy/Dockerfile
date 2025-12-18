FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

WORKDIR /app

# Copy and install requirements BEFORE copying code
# This enables Docker layer caching - requirements rarely change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the NER model so it's baked into the image
# This avoids downloading 431MB at runtime every time
RUN python -c "from transformers import AutoTokenizer, AutoModelForTokenClassification; \
    model_name = 'ugaray96/biobert_ncbi_disease_ner'; \
    AutoTokenizer.from_pretrained(model_name); \
    AutoModelForTokenClassification.from_pretrained(model_name)"

# Now copy application code
COPY *.py ./

# Create output directory
RUN mkdir -p /app/output

# This is just a placeholder for docs - we override with docker-compose
EXPOSE 8000

CMD ["python", "pmc_ner_pipeline.py"]
