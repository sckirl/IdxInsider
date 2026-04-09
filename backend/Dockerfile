FROM python:3.11-slim

WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    tesseract-ocr-ind \
    poppler-utils \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /backend/requirements.txt
RUN pip install --no-cache-dir -r /backend/requirements.txt
RUN playwright install chromium

# Copy backend code
COPY . /backend

# Expose port
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
