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

# Copy and install dependencies FIRST (before copying code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model into the image (so it doesn't download every run)
RUN python -c "from transformers import AutoTokenizer, AutoModelForTokenClassification; \
               model_name='ugaray96/biobert_ncbi_disease_ner'; \
               AutoTokenizer.from_pretrained(model_name); \
               AutoModelForTokenClassification.from_pretrained(model_name)"

# Copy code LAST (this changes frequently)
COPY . .

EXPOSE 8000
CMD ["python", "pmc_ner_pipeline.py"]
