from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from dotenv import load_dotenv
from app.db.database import init_db, dispose_engine
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
    description="API for managing lab reports and biomarker data",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
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
    "https://www.veindiagram.com", # Production domain with www
    "https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app", # Vercel preview deployment
    "https://vein-diagram.vercel.app", # Vercel production domain
    os.getenv("FRONTEND_URL", ""),  # Production frontend URL
]

# Remove any empty strings from origins
origins = [origin for origin in origins if origin]

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
    """
    Initialize database and check critical environment variables on startup.
    """
    try:
        # Check critical environment variables
        required_vars = {
            "DATABASE_URL": os.environ.get("DATABASE_URL", ""),
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            "SUPABASE_JWT_SECRET": os.environ.get("SUPABASE_JWT_SECRET", ""),
            "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
            "SUPABASE_SERVICE_KEY": os.environ.get("SUPABASE_SERVICE_KEY", "")
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            logger.error("Missing critical environment variables: %s", ", ".join(missing_vars))
            raise ValueError(f"Missing critical environment variables: {', '.join(missing_vars)}")
        
        # Initialize the database
        init_db()
        logger.info("Database initialized successfully")
        
        # Fix the pdfs table sequence
        try:
            from sqlalchemy import text
            from app.db.database import SessionLocal
            
            db = SessionLocal()
            # SQL to fix the sequence
            fix_sequence_sql = text("""
            DO $$
            DECLARE
                max_id INTEGER;
            BEGIN
                -- Get the maximum id from the pdfs table
                SELECT COALESCE(MAX(id), 0) INTO max_id FROM pdfs;
                
                -- Drop the existing sequence
                EXECUTE 'DROP SEQUENCE IF EXISTS pdfs_id_seq CASCADE';
                
                -- Create a new sequence starting from max_id + 1
                EXECUTE 'CREATE SEQUENCE pdfs_id_seq START WITH ' || (max_id + 1);
                
                -- Set the sequence as the default for the id column
                EXECUTE 'ALTER TABLE pdfs ALTER COLUMN id SET DEFAULT nextval(''pdfs_id_seq'')';
                
                -- Set the sequence ownership to the pdfs.id column
                EXECUTE 'ALTER SEQUENCE pdfs_id_seq OWNED BY pdfs.id';
                
                RAISE NOTICE 'Reset pdfs_id_seq to start from %', (max_id + 1);
            END $$;
            """)
            
            db.execute(fix_sequence_sql)
            db.commit()
            logger.info("Fixed pdfs table sequence successfully")
        except Exception as seq_error:
            logger.warning(f"Failed to fix pdfs sequence: {str(seq_error)}")
            # Don't raise the error, allow the application to start anyway
        
    except Exception as e:
        logger.error("Failed to initialize application: %s", str(e))
        raise

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Vein Diagram API",
        "version": "1.0.0",
        "description": "API for managing lab reports and biomarker data",
        "docs_url": "/docs" if os.getenv("ENVIRONMENT") != "production" else None,
        "redoc_url": "/redoc" if os.getenv("ENVIRONMENT") != "production" else None
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    Returns detailed health information in non-production environments.
    """
    health_info = {
        "status": "healthy",
        "version": "1.0.0",
    }
    
    # Add more detailed information for non-production environments
    if os.getenv("ENVIRONMENT") != "production":
        health_info.update({
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
        })
    
    return health_info

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

@app.on_event("shutdown")
async def shutdown_db_client():
    """
    Clean up database connections on shutdown.
    """
    try:
        dispose_engine()
        logger.info("Database connections cleaned up successfully")
    except Exception as e:
        logger.error("Error during database cleanup: %s", str(e))
        raise

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
