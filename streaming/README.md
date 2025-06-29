# 🛰️ Section 8: Advanced Streaming with "Cosmic Rover"

This section provides a focused, easy-to-understand example of advanced streaming concepts using a **"Cosmic Rover" Mission Control** theme. We'll explore how real-time data features are essential for communicating with and monitoring a rover on a distant planet.

## 🎯 Core Concepts Demonstrated

1.  **Streaming Large Responses**: Downloading a high-resolution image from the rover.
2.  **Server-Sent Events (SSE)**: Receiving a live telemetry feed of the rover's status.
3.  **Advanced WebSockets**: Creating separate communication channels for mission teams.
4.  **Upload with Progress**: Sending a new command sequence and monitoring its validation.

---

## 🚀 The "Cosmic Rover" Example

### 1. Streaming Response: The Rover Image Feed

-   **Analogy**: Sending a giant poster through a tiny mail slot. Instead of trying to shove the whole thing through at once (which would fail), you cut it into small, numbered puzzle pieces and send them one by one. The receiver assembles them on the other side.
-   **Concept**: `StreamingResponse` allows you to send data in chunks. This is ideal for large files (like images or videos) because the server doesn't need to load the entire file into memory. It reads and sends one chunk at a time, keeping memory usage low and starting the transmission almost instantly.
-   **Code Explanation**: The `/stream/rover-image` endpoint uses an `async` generator function (`image_chunk_generator`) that `yield`s small pieces of a simulated image file. Each piece is sent to the client as soon as it's ready.

    ```python
    @app.get("/stream/rover-image")
    async def stream_rover_image():
        """Streams a simulated high-resolution image from the rover chunk by chunk."""
        async def image_chunk_generator():
            for i in range(10):
                image_piece = f"[Chunk {i+1}/10: data.....]\n"
                yield image_piece.encode("utf-8")
                await asyncio.sleep(0.2)
        return StreamingResponse(image_chunk_generator(), media_type="text/plain")
    ```

### 2. Server-Sent Events (SSE): The Live Telemetry Feed

-   **Analogy**: A radio station broadcasting live news. The station sends out information continuously. Anyone with a radio can tune in and listen, but they can't talk back to the announcer. It's a one-way street of information.
-   **Concept**: SSE is a standard for servers to push real-time updates to clients over a single, long-lived HTTP connection. It's simpler than WebSockets and perfect for when you only need one-way data flow (from server to client).
-   **Code Explanation**: The `/stream/rover-telemetry` endpoint uses a generator that runs in an infinite loop. Every two seconds, it gathers new (simulated) rover data, formats it as an SSE message (`data: ...\n\n`), and `yield`s it to the client.

    ```python
    @app.get("/stream/rover-telemetry")
    async def stream_rover_telemetry():
        """Streams live telemetry data from the rover using Server-Sent Events (SSE)."""
        async def telemetry_generator():
            while True:
                telemetry_data = { "location": ..., "battery_level": ... }
                yield f"data: {json.dumps(telemetry_data)}\n\n"
                await asyncio.sleep(2)
        return StreamingResponse(telemetry_generator(), media_type="text/event-stream")
    ```

### 3. WebSockets: Mission Control Comms Channels

-   **Analogy**: A multi-channel walkie-talkie system. The Engineering team tunes into Channel 1, and the Science team tunes into Channel 2. They can talk and listen in real-time, but their conversations are kept separate.
-   **Concept**: WebSockets provide a full, two-way communication channel. A `ConnectionManager` class helps organize connections into separate "rooms" or "channels," allowing you to broadcast messages only to specific groups of clients.
-   **Code Explanation**: The `/ws/comms/{team_channel}` endpoint uses a `ConnectionManager` to manage different chat rooms. When a user connects, they are added to the list for their specific `team_channel`. When they send a message, it is broadcast only to the other users in that same channel.

    ```python
    class ConnectionManager:
        # ... methods to connect, disconnect, and broadcast to a room ...

    manager = ConnectionManager()

    @app.websocket("/ws/comms/{team_channel}")
    async def websocket_comms_endpoint(websocket: WebSocket, team_channel: str):
        await manager.connect(websocket, team_channel)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast_to_room(f"Message: {data}", team_channel)
        except WebSocketDisconnect:
            manager.disconnect(websocket, team_channel)
    ```

### 4. Upload with Progress: Validating Command Sequences

-   **Analogy**: Ordering a custom-built computer online. After you submit your order (upload the file), the website doesn't just go silent. It gives you live updates on a timeline: "Components Received," "Assembly in Progress," "Quality Testing," and finally "Shipped."
-   **Concept**: A client can upload a file, and the server can immediately start streaming back the progress of processing that file. This provides a much better user experience than a silent, long-running request, as the user gets immediate feedback on the server's progress.
-   **Code Explanation**: The `/upload/rover-commands` endpoint receives a file. It then immediately returns a `StreamingResponse` that runs a `progress_generator`. This generator simulates a multi-step validation process, `yield`ing a status update (using SSE format) to the client after each step completes.

    ```python
    @app.post("/upload/rover-commands")
    async def upload_rover_commands(file: UploadFile = File(...)):
        """Accepts a command sequence file and streams back the validation progress."""
        async def progress_generator():
            yield f"data: {json.dumps({'status': 'UPLOADING', 'detail': '...'})}\n\n"
            # ... loop through validation steps ...
            for step, duration in validation_steps:
                yield f"data: {json.dumps({'status': 'VALIDATING', 'detail': f'Step: {step}'})}\n\n"
                await asyncio.sleep(duration)
            yield f"data: {json.dumps({'status': 'COMPLETE', 'detail': '...'})}\n\n"
        return StreamingResponse(progress_generator(), media_type="text/event-stream")
    ```

---

## 🛠️ How to Run the Demo

1.  Make sure you have the required packages installed:
    ```bash
    pip install "fastapi[all]"
    ```
2.  From the **project root directory**, run the Uvicorn server:
    ```bash
    uvicorn streaming.main:app --reload
    ```
3.  Open your browser and navigate to [http://localhost:8000](http://localhost:8000) to see the Mission Control dashboard in action. 