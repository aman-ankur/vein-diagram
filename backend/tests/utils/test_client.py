"""
Custom TestClient implementation compatible with our specific versions:
- httpx 0.28.1
- starlette 0.36.3
- fastapi 0.110.0

This addresses the version incompatibility issue where httpx 0.27.0+ no longer
accepts the 'app' parameter in its Client constructor.
"""
import httpx
import asyncio
import typing
from app.main import app

class ASGITransportFixed:
    """Custom transport to handle ASGI applications with httpx 0.28.1+"""
    
    def __init__(self, app, raise_app_exceptions=True):
        self.app = app
        self.raise_app_exceptions = raise_app_exceptions
    
    async def handle_async_request(self, request):
        """Process an ASGI request and return the response"""
        # Convert httpx request to ASGI scope
        scope = {
            "type": "http",
            "method": request.method,
            "path": request.url.path,
            "root_path": "",
            "scheme": request.url.scheme,
            "query_string": request.url.query.encode("ascii"),
            "headers": [(k.lower().encode("ascii"), v.encode("ascii")) 
                        for k, v in request.headers.items()],
            "client": ("testclient", 50000),
            "server": (request.url.host, request.url.port or 80),
        }
        
        # Prepare response data
        response_status = None
        response_headers = None
        response_body = bytearray()
        
        # Create ASGI receive and send functions
        async def receive():
            if request.content:
                body = await request.aread()
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}
        
        async def send(message):
            nonlocal response_status, response_headers, response_body
            
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_body.extend(message.get("body", b""))
        
        # Call the ASGI app
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if self.raise_app_exceptions:
                raise exc from None
            
            # Handle the error if we're not raising exceptions
            response_status = 500
            response_headers = [(b"content-type", b"text/plain")]
            response_body = f"Internal Server Error: {str(exc)}".encode()
        
        # Ensure we have a valid status code
        if response_status is None:
            response_status = 500
            response_headers = [(b"content-type", b"text/plain")]
            response_body = b"Internal Server Error: No response returned"
        
        # Convert headers to dictionary
        headers = {}
        for key, value in response_headers:
            key = key.decode("ascii").lower()
            value = value.decode("ascii")
            headers[key] = value
        
        # Build and return the response
        return httpx.Response(
            status_code=response_status,
            headers=headers,
            content=bytes(response_body),
            request=request
        )
    
    def handle_request(self, request):
        """
        Handle request synchronously by running the async function in the event loop
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.handle_async_request(request))

# Create a test client using httpx with our custom transport
client = httpx.Client(
    transport=ASGITransportFixed(app),
    base_url="http://testserver"
) 