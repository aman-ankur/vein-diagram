import uvicorn
import os
from dotenv import load_dotenv
from app.db.init_db import init_db

# Load environment variables
load_dotenv()

# Get configuration from environment variables
host = os.getenv("API_HOST", "0.0.0.0")
port = int(os.getenv("API_PORT", "8000"))

if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Run the server
    uvicorn.run("app.main:app", host=host, port=port, reload=True) 