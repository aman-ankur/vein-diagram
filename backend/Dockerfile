# Use an official Python runtime as a parent image
# Using python 3.9 based on the venv structure seen in the file list
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required by pytesseract and pdf2image
# Also install build-essential and libpq-dev just in case psycopg2 or others need them
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    libpq-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
# Ensure .dockerignore is present in the backend directory to exclude unnecessary files
COPY . .

# Make port 8000 available to the world outside this container
# This is the port Uvicorn will listen on
EXPOSE 8000

# Run uvicorn server when the container launches
# Use 0.0.0.0 to allow connections from outside the container
# Use --host 0.0.0.0 to bind to all interfaces within the container
# The actual port mapping happens during deployment (e.g., Fly.io maps external port 443 to internal 8000)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
