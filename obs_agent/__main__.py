"""Entry point for ObsAgent."""

import argparse
import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    """Run the ObsAgent server."""
    parser = argparse.ArgumentParser(description="ObsAgent Server")
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port to bind (default: 8080)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    uvicorn.run(
        "obs_agent.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
