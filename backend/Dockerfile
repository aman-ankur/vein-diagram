# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by pytesseract and pdf2image
# Also install build-essential and libpq-dev just in case psycopg2 or others need them
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    libpq-dev \
    iputils-ping \
    curl \
    dnsutils \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache usage
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Create and set permissions for necessary directories
RUN mkdir -p /app/logs && \
    chmod 755 /app/logs

# Copy and set permissions for the start script
COPY start.sh .
RUN chmod +x start.sh

# Expose the port the app runs on
EXPOSE 8000

# Run the start script
CMD ["./start.sh"]
