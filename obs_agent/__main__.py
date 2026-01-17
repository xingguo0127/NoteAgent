"""Entry point for ObsAgent."""

import os

import uvicorn
from dotenv import load_dotenv

load_dotenv()


def main():
    """Run the ObsAgent server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(
        "obs_agent.api.app:app",
        host=host,
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
