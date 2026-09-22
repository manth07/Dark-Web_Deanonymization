FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download spaCy models and NLTK data for zero-network execution
RUN python -m spacy download en_core_web_sm \
    && python -m nltk.downloader punkt punkt_tab stopwords

# Copy application source code
COPY . /app

# Default command
CMD ["python", "main.py", "run-worker"]
