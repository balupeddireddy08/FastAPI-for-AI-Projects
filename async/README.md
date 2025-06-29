# 🚀 Section 7: Simplified Async Programming with FastAPI

This section provides a clear and simple demonstration of FastAPI's core asynchronous features. We've replaced the complex gaming platform with a minimal application to make learning easier.

## 🎯 What You'll Learn

-   **`async def` Endpoints**: The foundation of non-blocking APIs in FastAPI.
-   **Concurrent Operations**: How to perform multiple I/O-bound tasks at the same time using `asyncio.gather`.
-   **Background Tasks**: Executing long-running jobs without making the client wait for a response.
-   **Streaming Responses**: Sending data to the client continuously with Server-Sent Events (SSE).
-   **WebSockets**: Enabling real-time, bidirectional communication for features like live chat.

---

## 🛠️ Running The Demo

1.  **Navigate to the directory:**
    ```bash
    cd 07-async
    ```

2.  **Install dependencies:**
    ```bash
    pip install "fastapi[all]"
    ```

3.  **Run the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```
    The server will be running at `http://localhost:8000`.

---

## 💻 Code Examples & Endpoints

Here are the simplified examples you can find in `main.py`.

### 1. Basic Async Endpoint

An `async` function that simulates a 1-second delay. This shows how FastAPI can handle other requests while waiting for a slow operation to finish.

```python
@app.get("/async-sleep")
async def basic_async_sleep():
    await asyncio.sleep(1)
    return {"message": "Slept for 1 second!"}
```

**Try it:** Visit [http://localhost:8000/async-sleep](http://localhost:8000/async-sleep)

### 2. Concurrent Tasks

This endpoint calls two different async functions that simulate slow network calls. Instead of running them one after another (sequentially), `asyncio.gather` runs them at the same time (concurrently).

```python
async def fetch_data_from_service_one():
    await asyncio.sleep(1)
    return {"service": "one", "data": "some data"}

async def fetch_data_from_service_two():
    await asyncio.sleep(1.5)
    return {"service": "two", "data": "more data"}

@app.get("/concurrent-requests")
async def run_concurrent_requests():
    # Total time will be ~1.5 seconds, not 2.5 seconds
    results = await asyncio.gather(
        fetch_data_from_service_one(),
        fetch_data_from_service_two()
    )
    return {"results": results}
```

**Try it:** Visit [http://localhost:8000/concurrent-requests](http://localhost:8000/concurrent-requests)

### 3. Background Tasks

This endpoint returns a response to the user immediately while starting a long-running task in the background. Useful for sending emails, processing data, etc.

```python
async def write_log_file(message: str):
    await asyncio.sleep(3) # Simulate a slow task
    with open("app.log", "a") as log_file:
        log_file.write(f"{datetime.now()}: {message}\\n")

@app.post("/send-notification/")
async def send_notification(email: str, message: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        write_log_file, f"Notification to {email}: {message}"
    )
    return {"message": "Notification sent in the background"}
```

**Try it:** Send a POST request to `http://localhost:8000/send-notification/`. Check your terminal and the `app.log` file created in the directory.

### 4. Streaming Response (Server-Sent Events)

This endpoint streams the current server time to the client every second without closing the connection.

```python
@app.get("/stream-time")
async def stream_time():
    async def time_generator():
        while True:
            time_str = datetime.now().strftime("%H:%M:%S")
            yield f"data: {{\"time\": \"{time_str}\"}}\\n\\n"
            await asyncio.sleep(1)

    return StreamingResponse(time_generator(), media_type="text/event-stream")
```

**Try it:** Visit [http://localhost:8000/stream-time](http://localhost:8000/stream-time). You will see the time update every second.

### 5. WebSocket Chat

A simple chat application demonstrating real-time, two-way communication with WebSockets.

```python
class ConnectionManager:
    # ... (manages WebSocket connections)

manager = ConnectionManager()

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"A user says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user has left the chat.")
```

**Try it:** Open [http://localhost:8000/chat-demo](http://localhost:8000/chat-demo) in multiple browser tabs and send messages. 