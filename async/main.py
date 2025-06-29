import asyncio
import json
from datetime import datetime
from typing import List

from fastapi import (FastAPI, BackgroundTasks, WebSocket,
                     WebSocketDisconnect)
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI(
    title="🚀 FastAPI Async Features Demo",
    description="A simple app to demonstrate key asynchronous features of FastAPI.",
    version="1.0.0",
)

# =================================================================
# 1. Basic Async Endpoint
# =================================================================


@app.get("/async-sleep")
async def basic_async_sleep():
    """
    Demonstrates a basic async endpoint.
    This endpoint simulates a slow network call that takes 1 second.
    FastAPI can handle other requests while waiting for this to complete.
    """
    await asyncio.sleep(1)
    return {"message": "Slept for 1 second!"}


# =================================================================
# 2. Concurrent Tasks with asyncio.gather
# =================================================================


async def fetch_data_from_service_one():
    """Simulates fetching data from a slow external service."""
    print("Fetching data from service one...")
    await asyncio.sleep(1)
    print("Finished fetching from service one.")
    return {"service": "one", "data": "some data"}


async def fetch_data_from_service_two():
    """Simulates fetching data from another slow external service."""
    print("Fetching data from service two...")
    await asyncio.sleep(1.5)
    print("Finished fetching from service two.")
    return {"service": "two", "data": "more data"}


@app.get("/concurrent-requests")
async def run_concurrent_requests():
    """
    Demonstrates running multiple async operations concurrently.
    Instead of waiting 1s + 1.5s = 2.5s, it will take ~1.5s (the longest task).
    """
    print("Starting concurrent requests.")
    # Using asyncio.gather to run tasks concurrently
    results = await asyncio.gather(
        fetch_data_from_service_one(),
        fetch_data_from_service_two()
    )
    print("Finished concurrent requests.")
    return {"results": results}


# =================================================================
# 3. Background Tasks
# =================================================================


async def write_log_file(message: str):
    """A slow I/O operation to run in the background."""
    print(f"Background task: Starting to write log '{message}'")
    await asyncio.sleep(3)  # Simulate slow file write
    with open("app.log", "a") as log_file:
        log_file.write(f"{datetime.now()}: {message}\n")
    print("Background task: Finished writing log.")


@app.post("/send-notification/")
async def send_notification(email: str, message: str, background_tasks: BackgroundTasks):
    """
    Demonstrates running a task in the background.
    The client gets an immediate response, and the server continues
    processing the `write_log_file` function.
    """
    background_tasks.add_task(
        write_log_file, f"Notification sent to {email}: {message}")
    return {"message": "Notification is being sent in the background"}


# =================================================================
# 4. Streaming Response (Server-Sent Events)
# =================================================================


@app.get("/stream-time")
async def stream_time():
    """
    Demonstrates streaming data from the server to the client (Server-Sent Events).
    The connection stays open, and the server sends an update every second.
    """
    async def time_generator():
        while True:
            time_str = datetime.now().strftime("%H:%M:%S")
            event_data = {"time": time_str}
            # The data must be in a specific format for SSE
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(time_generator(), media_type="text/event-stream")


# =================================================================
# 5. WebSocket for Real-time Communication
# =================================================================


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    """
    Demonstrates a real-time chat using WebSockets.
    Multiple clients can connect, and messages are broadcast to everyone.
    """
    await manager.connect(websocket)
    await manager.broadcast("A new user has joined the chat.")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"A user says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user has left the chat.")


@app.get("/chat-demo")
def get_chat_demo():
    """A simple HTML page to demonstrate the WebSocket chat."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Chat</title>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <ul id='messages'>
            </ul>
            <form onsubmit="sendMessage(event)">
                <input type="text" id="messageText" autocomplete="off"/>
                <button>Send</button>
            </form>
            <script>
                var ws = new WebSocket("ws://localhost:8000/ws/chat");
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                function sendMessage(event) {
                    var input = document.getElementById("messageText")
                    ws.send(input.value)
                    input.value = ''
                    event.preventDefault()
                }
            </script>
        </body>
    </html>
    """)

# To run this file:
# 1. Make sure you have fastapi and uvicorn installed:
#    pip install "fastapi[all]"
# 2. Run the server:
#    uvicorn main:app --reload