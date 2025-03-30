import os
import sys
import time
import json
import logging
import threading
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def check_env_vars():
    """Check for required environment variables."""
    logger.info("Checking environment variables...")
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        env_loaded = load_dotenv()
        logger.info(f".env file loaded: {env_loaded}")
    except ImportError:
        logger.warning("python-dotenv not installed. Cannot load .env file automatically.")
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        logger.info(f"ANTHROPIC_API_KEY is set (length: {len(api_key)})")
    else:
        logger.error("ANTHROPIC_API_KEY is not set!")
        return False
    
    return True

def test_api_call_with_timeout(timeout=30):
    """Test Claude API call with timeout."""
    logger.info(f"Testing Claude API call with {timeout}s timeout...")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("No API key available!")
        return False
    
    result = [None]
    exception = [None]
    
    def make_api_call():
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("Creating Anthropic client...")
            
            # Send a simple message
            logger.info("Sending test message to Claude API...")
            start_time = time.time()
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Use the smallest model for quick testing
                max_tokens=10,
                temperature=0,
                system="You are a helpful AI assistant.",
                messages=[
                    {"role": "user", "content": "Say hello."}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Received response in {elapsed:.2f} seconds")
            logger.info(f"Response content: {response.content[0].text}")
            result[0] = True
        except Exception as e:
            logger.error(f"API call error: {str(e)}", exc_info=True)
            exception[0] = e
            result[0] = False
    
    # Create and start thread
    thread = threading.Thread(target=make_api_call)
    thread.daemon = True
    thread.start()
    
    # Wait for thread to complete or timeout
    thread.join(timeout)
    
    # Check if thread is still alive (timeout occurred)
    if thread.is_alive():
        logger.error(f"API call timed out after {timeout} seconds")
        return False
    
    # Check if there was an exception
    if exception[0]:
        logger.error(f"API call raised an exception: {str(exception[0])}")
        return False
    
    return result[0]

def check_network_connectivity():
    """Check network connectivity to Claude API endpoint."""
    logger.info("Checking network connectivity...")
    
    try:
        import socket
        import ssl
        
        # Try to connect to Claude API endpoint
        host = "api.anthropic.com"
        port = 443
        
        # Create socket
        logger.info(f"Testing connection to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)  # Increased timeout from 5 to 15 seconds
        
        # Wrap socket with SSL
        context = ssl.create_default_context()
        wrapped_socket = context.wrap_socket(sock, server_hostname=host)
        
        # Connect to host
        start_time = time.time()
        wrapped_socket.connect((host, port))
        elapsed = time.time() - start_time
        
        logger.info(f"Successfully connected to {host}:{port} in {elapsed:.2f} seconds")
        wrapped_socket.close()
        return True
    except Exception as e:
        logger.error(f"Network connectivity test failed: {str(e)}")
        return False

def check_proxy_settings():
    """Check if proxy settings might be interfering."""
    logger.info("Checking proxy settings...")
    
    proxy_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
    found_proxies = []
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            found_proxies.append(f"{var}={value}")
    
    if found_proxies:
        logger.warning(f"Found proxy settings that might affect connections: {', '.join(found_proxies)}")
    else:
        logger.info("No proxy settings found in environment variables.")

def main():
    """Main function to run all tests."""
    logger.info("Starting Claude API connection test")
    
    # Check environment variables
    if not check_env_vars():
        logger.error("Environment check failed")
        return False
    
    # Check network connectivity
    if not check_network_connectivity():
        logger.error("Network connectivity check failed")
        return False
    
    # Check proxy settings
    check_proxy_settings()
    
    # Test API call
    success = test_api_call_with_timeout(timeout=45)
    
    if success:
        logger.info("All tests passed! Claude API connection is working.")
        return True
    else:
        logger.error("Claude API connection test failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 