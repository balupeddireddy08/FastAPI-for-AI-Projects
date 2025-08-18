import asyncio
import json
import random
from datetime import datetime
from typing import Dict, List

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse, StreamingResponse
import aiofiles

# --- App Setup ---
# This creates our main application, with a clear title and description
# for our new "Cosmic Rover" Mission Control theme.
app = FastAPI(
    title="🛰️ Cosmic Rover - Mission Control API",
    description="""
    This API simulates a Mission Control dashboard for a cosmic rover,
    demonstrating advanced real-time streaming features in FastAPI.
    """,
    version="2.0.0",
)


# ===================================================================================
# FEATURE 1: Streaming Response for Large Data (Rover Image)
# ===================================================================================
# ANALOGY: Sending a giant poster through a tiny mail slot.
# Instead of trying to shove the whole poster through at once (which would fail),
# you cut it into small, numbered puzzle pieces and send them one by one.
# The receiver assembles them on the other side.
#
# CONCEPT: `StreamingResponse` allows you to send data in chunks. This is ideal
# for large files (like images, videos, or big data exports) because the server
# doesn't need to load the entire file into memory. It reads and sends one
# chunk at a time, keeping memory usage low and starting the transmission instantly.

@app.get("/stream/rover-image")
async def stream_rover_image():
    """
    Streams a real image from the local filesystem chunk by chunk.
    """
    # An 'async generator' function that yields data pieces.
    async def image_chunk_generator():
        # Using aiofiles to read the file asynchronously to prevent blocking.
        async with aiofiles.open("rover_image.jpg", mode="rb") as f:
            while chunk := await f.read(4096):  # Read in 4KB chunks
                yield chunk
    
    # The media type is now 'image/jpeg' to tell the browser how to handle the data.
    return StreamingResponse(image_chunk_generator(), media_type="image/jpeg")


# ===================================================================================
# FEATURE 2: Server-Sent Events (SSE) for Live Telemetry
# ===================================================================================
# ANALOGY: A radio station broadcasting live news.
# The station sends out information continuously. Anyone with a radio can tune in
# and listen, but they can't talk back. It's a one-way street of information.
#
# CONCEPT: Server-Sent Events (SSE) are a standard way for a server to push
# real-time updates to a client over a single, long-lived HTTP connection.
# The client just listens for messages. It's simpler than WebSockets when you
# only need one-way data flow (server -> client).

@app.get("/stream/rover-telemetry")
async def stream_rover_telemetry():
    """
    Streams live telemetry data from the rover using Server-Sent Events (SSE).
    """
    async def telemetry_generator():
        # A simple model of the rover's state.
        rover_location = {"x": 10.5, "y": 25.1}
        
        while True:
            # Simulate slight movements and fluctuations.
            rover_location["x"] += random.uniform(-0.1, 0.1)
            rover_location["y"] += random.uniform(-0.1, 0.1)
            
            telemetry_data = {
                "timestamp": datetime.now().isoformat(),
                "location": rover_location,
                "battery_level": round(95.5 - random.uniform(0, 0.5), 2),
                "signal_strength": random.randint(-80, -65),
            }
            # The SSE protocol requires data to be in the format "data: <message>\n\n".
            # We serialize our dictionary to a JSON string.
            yield f"data: {json.dumps(telemetry_data)}\n\n"
            # Send an update every two seconds.
            await asyncio.sleep(2)
    
    return StreamingResponse(telemetry_generator(), media_type="text/event-stream")


# ===================================================================================
# FEATURE 3: WebSockets for Team Comms (Room-Based Chat)
# ===================================================================================
# ANALOGY: A multi-channel walkie-talkie system.
# The Engineering team tunes into Channel 1, and the Science team tunes into
# Channel 2. They can talk and listen in real-time, but their conversations
# are kept separate. The ConnectionManager is the operator directing traffic.
#
# CONCEPT: WebSockets provide a full, two-way communication channel between
# the client and server. A Connection Manager class helps organize connections,
# for example, by grouping them into "rooms" so you can broadcast messages
# only to specific clients.

class ConnectionManager:
    """Manages WebSocket connections for different team channels."""
    def __init__(self):
        # A dictionary to hold connections for each room (e.g., 'science', 'engineering').
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_name: str):
        await websocket.accept()
        if room_name not in self.active_connections:
            self.active_connections[room_name] = []
        self.active_connections[room_name].append(websocket)

    def disconnect(self, websocket: WebSocket, room_name: str):
        if room_name in self.active_connections:
            self.active_connections[room_name].remove(websocket)

    async def broadcast_to_room(self, message: str, room_name: str):
        if room_name in self.active_connections:
            for connection in self.active_connections[room_name]:
                await connection.send_text(message)

# Create a single manager to handle all our WebSocket connections.
manager = ConnectionManager()

@app.websocket("/ws/comms/{team_channel}")
async def websocket_comms_endpoint(websocket: WebSocket, team_channel: str):
    """Handles WebSocket connections for a specific team's comms channel."""
    await manager.connect(websocket, team_channel)
    # Announce the new connection to the specific team channel.
    await manager.broadcast_to_room(f"A new user has joined the '{team_channel}' channel.", team_channel)
    try:
        # Loop indefinitely, waiting for messages from the client.
        while True:
            data = await websocket.receive_text()
            # Broadcast the received message to everyone else in the same room.
            message = f"[User-{websocket.client.port}] says: {data}"
            await manager.broadcast_to_room(message, team_channel)
    except WebSocketDisconnect:
        # When a client disconnects, clean up and notify the room.
        manager.disconnect(websocket, team_channel)
        await manager.broadcast_to_room(f"A user has left the '{team_channel}' channel.", team_channel)


# ===================================================================================
# Demo HTML Page
# ===================================================================================

@app.get("/", response_class=HTMLResponse)
def get_mission_control_dashboard():
    """Serves the main Mission Control HTML page."""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse("<h1>Error: index.html not found</h1>")

# To run this file from the project root:
# uvicorn streaming.main:app --reload