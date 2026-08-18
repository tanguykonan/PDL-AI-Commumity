FROM python:3.11-slim-bookworm
LABEL authors="NYTHIQUE"

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/PDL-AI

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

CMD ["python", "run.py"]