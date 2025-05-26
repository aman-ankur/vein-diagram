#!/bin/bash

# Vein Diagram Backend Startup Script with Environment Loading
# This script ensures all environment variables are properly loaded before starting the application

set -e  # Exit on any error

echo "🚀 Starting Vein Diagram Backend with Environment Loading..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in backend directory"
    echo "Please create a .env file with required environment variables"
    echo "Required variables: ANTHROPIC_API_KEY, DATABASE_URL, SUPABASE_URL, etc."
    exit 1
fi

# Load environment variables from .env file
echo "📁 Loading environment variables from .env file..."
export $(grep -v '^#' .env | xargs)

# Verify critical environment variables
echo "🔍 Verifying critical environment variables..."

# Check ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set in .env file"
    exit 1
else
    echo "✅ ANTHROPIC_API_KEY is set (length: ${#ANTHROPIC_API_KEY})"
fi

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Warning: DATABASE_URL not set, will use default SQLite"
else
    echo "✅ DATABASE_URL is set"
fi

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "Consider activating your virtual environment first"
else
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
fi

# Install/update dependencies if requirements.txt is newer than last install
if [ requirements.txt -nt .last_install ] || [ ! -f .last_install ]; then
    echo "📦 Installing/updating dependencies..."
    pip install -r requirements.txt
    touch .last_install
else
    echo "✅ Dependencies are up to date"
fi

# Test Claude API connection
echo "🧪 Testing Claude API connection..."
python -c "
import os
import anthropic
try:
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    response = client.messages.create(
        model='claude-3-5-sonnet-20241022',
        max_tokens=10,
        messages=[{'role': 'user', 'content': 'Test'}]
    )
    print('✅ Claude API connection successful')
except Exception as e:
    print(f'❌ Claude API connection failed: {e}')
    exit(1)
"

# Start the application
echo "🎯 Starting FastAPI application..."
echo "Environment: $(python -c "import os; print(os.environ.get('ENVIRONMENT', 'development'))")"
echo "API Host: $(python -c "import os; print(os.environ.get('API_HOST', '0.0.0.0'))")"
echo "API Port: $(python -c "import os; print(os.environ.get('API_PORT', '8000'))")"

# Use environment variables for host and port, with defaults
HOST=${API_HOST:-0.0.0.0}
PORT=${API_PORT:-8000}

echo "🌐 Server will be available at: http://$HOST:$PORT"
echo "📚 API Documentation: http://$HOST:$PORT/docs"
echo "🔄 Health Check: http://$HOST:$PORT/health"

# Start uvicorn with proper configuration
exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload \
    --log-level info \
    --access-log \
    --use-colors 