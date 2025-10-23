#!/usr/bin/env python3
"""
Startup script for Railway deployment
Reads PORT from environment and starts uvicorn
"""
import os
import sys

if __name__ == "__main__":
    # Get PORT from environment, default to 8000
    port_str = os.environ.get("PORT", "8000")
    print(f"PORT environment variable: {port_str}", flush=True)

    try:
        port = int(port_str)
        print(f"Starting uvicorn on port {port}...", flush=True)
    except ValueError as e:
        print(f"ERROR: Invalid PORT value '{port_str}': {e}", flush=True)
        sys.exit(1)

    # Check critical environment variables
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", flush=True)
        print("Please set these in Railway dashboard → Variables tab", flush=True)
        sys.exit(1)

    print(f"✓ DATABASE_URL: configured", flush=True)
    print(f"✓ SECRET_KEY: configured", flush=True)
    print(f"✓ All required environment variables present", flush=True)

    # Import and run uvicorn programmatically
    try:
        import uvicorn
        print("✓ uvicorn imported successfully", flush=True)

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    except Exception as e:
        print(f"ERROR starting uvicorn: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
