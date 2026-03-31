"""
FastAPI application entrypoint.
"""

import os

import socketio
from fastapi import FastAPI

from chatty.core.database import create_tables
from chatty.core.logging import configure_logging, get_logger
from chatty.core.middleware import ErrorLoggingMiddleware, LoggingMiddleware
from chatty.routers import chatroom_participants, chatrooms, health, hello, messages, users

# Configure logging
configure_logging()
logger = get_logger("main")

cors_raw = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
cors_origins = "*" if cors_raw == "*" else [o.strip() for o in cors_raw.split(",")]

sio = socketio.AsyncServer(cors_allowed_origins=cors_origins, async_mode="asgi")


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client {sid} connected")


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client {sid} disconnected")


@sio.event
async def join(sid, data):
    """Handle client joining a chatroom."""
    try:
        user_id = data.get("user_id")
        chatroom_id = data.get("chatroom_id")

        if not user_id or not chatroom_id:
            await sio.emit("error", {"message": "user_id and chatroom_id are required"}, room=sid)
            return

        # Join the room using chatroom_id as the room identifier
        await sio.enter_room(sid, chatroom_id)
        logger.info(f"Client {sid} (user {user_id}) joined chatroom {chatroom_id}")

        # Acknowledge the join
        await sio.emit("joined", {"chatroom_id": chatroom_id}, room=sid)

    except Exception as e:
        # TODO: Implement proper error handling for Socket.IO events
        logger.error(f"Error in join event: {e}")
        await sio.emit("error", {"message": "An error occurred"}, room=sid)


@sio.event
async def leave(sid, data):
    """Handle client leaving a chatroom."""
    try:
        user_id = data.get("user_id")
        chatroom_id = data.get("chatroom_id")

        if not user_id or not chatroom_id:
            await sio.emit("error", {"message": "user_id and chatroom_id are required"}, room=sid)
            return

        # Leave the room
        await sio.leave_room(sid, chatroom_id)
        logger.info(f"Client {sid} (user {user_id}) left chatroom {chatroom_id}")

        # Acknowledge the leave
        await sio.emit("left", {"chatroom_id": chatroom_id}, room=sid)

    except Exception as e:
        # TODO: Implement proper error handling for Socket.IO events
        logger.error(f"Error in leave event: {e}")
        await sio.emit("error", {"message": "An error occurred"}, room=sid)


app = FastAPI(
    title="Chatty Backend",
    description="Chatty Backend experimentation",
    version="0.1.0",
)

# Add logging middleware
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(LoggingMiddleware)


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on application startup."""
    logger.info("Starting up Chatty Backend application")

    # Clean out existing database and create fresh tables
    from chatty.core.database import Base, engine

    Base.metadata.drop_all(bind=engine)  # Drop all existing tables
    logger.info("Existing database tables dropped")

    create_tables()
    logger.info("Fresh database tables created successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Shutting down Chatty Backend application")


# Create Socket.IO ASGI app
socketio_app = socketio.ASGIApp(sio, app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(hello.router, prefix="/hello", tags=["hello"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(chatrooms.router, prefix="/chatrooms", tags=["chatrooms"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(chatroom_participants.router, prefix="/chatroom-participants", tags=["chatroom-participants"])

# Set Socket.IO server in messages router for event emission
messages.set_socketio_server(sio)

# Mount Socket.IO app
app.mount("/socket.io/", socketio_app)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Welcome to Chatty Backend!"}
