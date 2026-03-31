"""
Script to run the FastAPI application.
"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", "8000"))
    uvicorn.run(
        "chatty.main:socketio_app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

