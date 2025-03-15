#!/bin/bash
# Script to run tests for the biomarker extraction system

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables for testing
export PYTHONPATH=.
export ANTHROPIC_API_KEY="dummy_key_for_testing"

# Clean previous test results
rm -rf .coverage htmlcov

echo "Running unit tests..."
python3 -m pytest -v tests/services/ --cov=app/services

echo "Running API tests..."
python3 -m pytest -v tests/api/ --cov=app/api

echo "Running integration tests..."
python3 -m pytest -v tests/integration/ --cov=app

echo "Running end-to-end tests..."
python3 -m pytest -v tests/end_to_end/ --cov=app

echo "Generating coverage report..."
python3 -m pytest --cov=app --cov-report=html

echo "Tests completed. Coverage report available in htmlcov/index.html" 