#!/usr/bin/env python3
"""
Startup script for Railway deployment
Reads PORT from environment and starts uvicorn
"""
import os
import sys

if __name__ == "__main__":
    # Get PORT from environment, default to 8000
    port = int(os.environ.get("PORT", "8000"))

    print(f"Starting uvicorn on port {port}...", flush=True)

    # Import and run uvicorn programmatically
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
