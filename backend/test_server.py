#!/usr/bin/env python3

import requests
import time
import subprocess
import sys
import signal
import os

def test_server():
    print("Testing server connectivity...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "main:app", 
        "--host", "127.0.0.1", "--port", "8001"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test root endpoint
        response = requests.get("http://127.0.0.1:8001/", timeout=5)
        print(f"✅ Server responding: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test docs endpoint
        docs_response = requests.get("http://127.0.0.1:8001/docs", timeout=5)
        print(f"✅ Docs available: {docs_response.status_code}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not responding: {e}")
        return False
        
    finally:
        # Clean up
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    success = test_server()
    if success:
        print("\n🎉 Server is working! You can now run:")
        print("   python run_server.py")
        print("   Or: python -m uvicorn main:app --host 127.0.0.1 --port 8001")
    else:
        print("\n❌ Server test failed.")