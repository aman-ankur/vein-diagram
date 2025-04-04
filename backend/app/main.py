from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv
from app.db.init_db import init_db
from fastapi.responses import JSONResponse, FileResponse
import glob
from app.core.logging_config import setup_logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

# Set up logging configuration
setup_logging()
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Environment loaded")

# Import routers
from app.api.routes import pdf_routes, biomarker_routes, profile_routes

# Import auth middleware
from app.core.auth import get_current_user, get_optional_current_user

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Skip logging for health check endpoints
        if not request.url.path.endswith('/health'):
            # Get client IP and query parameters
            client_host = request.client.host if request.client else "unknown"
            query_string = str(request.query_params) if request.query_params else ""
            status_phrase = "OK" if response.status_code == 200 else response.status_code
            
            logger.info(
                f'{client_host} - "{request.method} {request.url.path}{query_string} HTTP/1.1" {response.status_code} {status_phrase}'
            )
        
        return response

# Create FastAPI app
app = FastAPI(
    title="Vein Diagram API",
    description="API for processing blood test PDFs and generating visualizations",
    version="0.1.0",
    redirect_slashes=False  # Disable automatic slash redirects
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
# Define allowed origins for development and production
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3002",
    "http://localhost:3005",
    "http://localhost:5173",  # Vite default dev server
    "https://veindiagram.com", # Production domain
    "https://www.veindiagram.com" # Production domain with www
]

# Optionally add FRONTEND_URL from environment if it's set and not already in the list
# This provides flexibility but explicit listing is generally safer for production.
# frontend_url_env = os.environ.get("FRONTEND_URL")
# if frontend_url_env and frontend_url_env not in origins:
#     origins.append(frontend_url_env)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"],  # Expose Authorization header for token handling
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Include routers with explicit paths for both with and without trailing slash
app.include_router(pdf_routes.router, prefix="/api/pdf", tags=["PDF Processing"])
app.include_router(biomarker_routes.router, prefix="/api", tags=["Biomarker Data"])
app.include_router(profile_routes.router, prefix="/api/profiles", tags=["Profile Management"])

# Authentication test endpoint
@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Test endpoint to check authentication and get current user info.
    """
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "authenticated": True
    }

# Initialize the database at startup
@app.on_event("startup")
async def startup_db_client():
    # Check critical environment variables
    database_url = os.environ.get("DATABASE_URL", "")
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    supabase_jwt_secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    
    if not all([database_url, anthropic_api_key, supabase_jwt_secret]):
        logger.error("Missing critical environment variables")
        if not database_url:
            logger.error("DATABASE_URL is not set")
        if not anthropic_api_key:
            logger.error("ANTHROPIC_API_KEY is not set")
        if not supabase_jwt_secret:
            logger.error("SUPABASE_JWT_SECRET is not set")
    
    # Initialize the database
    init_db()
    logger.info("Database initialized")

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
