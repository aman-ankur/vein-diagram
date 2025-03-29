from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv
from app.db.init_db import init_db
from fastapi.responses import JSONResponse, FileResponse
import glob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Loaded environment variables from .env file")

# Import routers
from app.api.routes import pdf_routes, biomarker_routes, profile_routes

# Create FastAPI app
app = FastAPI(
    title="Vein Diagram API",
    description="API for processing blood test PDFs and generating visualizations",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Include frontend development URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include routers
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Processing"])
app.include_router(biomarker_routes.router, prefix="/api", tags=["Biomarker Data"])
app.include_router(profile_routes.router, prefix="/api/profiles", tags=["Profile Management"])

# Initialize the database at startup
@app.on_event("startup")
async def startup_db_client():
    # Debug environment variables
    logger.info("Checking critical environment variables:")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    database_url = os.environ.get("DATABASE_URL", "")
    
    logger.info(f"DATABASE_URL is {'set' if database_url else 'NOT SET'}")
    logger.info(f"ANTHROPIC_API_KEY is {'set (length: ' + str(len(anthropic_api_key)) + ')' if anthropic_api_key else 'NOT SET'}")
    
    # Initialize the database
    init_db()
    logger.info("Database initialized at startup")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Vein Diagram API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Debug endpoints for developers
@app.get("/debug/logs", tags=["Debug"])
async def get_log_files():
    """
    Get a list of available log files for debugging.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    logs = glob.glob(os.path.join(log_dir, "*.txt")) + glob.glob(os.path.join(log_dir, "*.log"))
    return {"log_files": [os.path.basename(log) for log in logs]}

@app.get("/debug/logs/{filename}", tags=["Debug"])
async def get_log_file(filename: str):
    """
    Get the contents of a specific log file.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    file_path = os.path.join(log_dir, filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return JSONResponse(status_code=404, content={"error": f"Log file {filename} not found"})
    
    return FileResponse(file_path)

@app.get("/debug/claude_responses", tags=["Debug"])
async def get_claude_responses():
    """
    Get a list of available Claude API response files for debugging.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    responses = glob.glob(os.path.join(log_dir, "claude_response_*.txt"))
    return {"response_files": [os.path.basename(r) for r in responses]}

@app.get("/debug/claude_responses/{filename}", tags=["Debug"])
async def get_claude_response(filename: str):
    """
    Get the contents of a specific Claude API response file.
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    file_path = os.path.join(log_dir, filename)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return JSONResponse(status_code=404, content={"error": f"Response file {filename} not found"})
    
    return FileResponse(file_path)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 