#!/usr/bin/env python3

import uvicorn
import os
import sys

if __name__ == "__main__":
    print("Starting SnapMerge Server...")
    print("Server will be available at: http://127.0.0.1:8001")
    print("API docs at: http://127.0.0.1:8001/docs")
    print("Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)