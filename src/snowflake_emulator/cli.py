"""
Command-line interface to start the Snowflake Emulator server.
"""

import argparse
import sys
import uvicorn
from snowflake_emulator.config import settings


def main():
    parser = argparse.ArgumentParser(description="Snowflake Emulator Server")
    parser.add_argument("--host", default=settings.host, help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to (default: 8080)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    print(f"❄️ Starting Snowflake Emulator on http://{args.host}:{args.port}")
    uvicorn.run("snowflake_emulator.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
