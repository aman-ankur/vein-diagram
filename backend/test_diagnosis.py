"""
Diagnostic script to identify TestClient initialization issue.
"""
import inspect
import sys

print(f"Python version: {sys.version}")

try:
    from starlette.testclient import TestClient as StarletteTestClient
    print("Starlette TestClient successfully imported")
    print(f"Starlette TestClient init signature: {inspect.signature(StarletteTestClient.__init__)}")
except Exception as e:
    print(f"Error importing Starlette TestClient: {e}")

try:
    from fastapi.testclient import TestClient as FastAPITestClient
    print("FastAPI TestClient successfully imported")
    print(f"FastAPI TestClient init signature: {inspect.signature(FastAPITestClient.__init__)}")
except Exception as e:
    print(f"Error importing FastAPI TestClient: {e}")

try:
    import httpx
    print("httpx successfully imported")
    print(f"httpx.Client init signature: {inspect.signature(httpx.Client.__init__)}")
except Exception as e:
    print(f"Error importing httpx: {e}")

try:
    from app.main import app
    print("App successfully imported")
    print(f"App type: {type(app)}")
except Exception as e:
    print(f"Error importing app: {e}")

try:
    from starlette.testclient import TestClient
    client = TestClient(app)
    print("TestClient successfully initialized with app as positional argument")
except Exception as e:
    print(f"Error initializing TestClient with app as positional argument: {e}")

try:
    from starlette.testclient import TestClient
    client = TestClient(app=app)
    print("TestClient successfully initialized with app as keyword argument")
except Exception as e:
    print(f"Error initializing TestClient with app as keyword argument: {e}")

print("Diagnosis complete") 