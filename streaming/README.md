# 🎬 Section 8: Streaming - StreamVerse Live Content Platform

Master **streaming and real-time data** by building a live content platform! Learn how to handle large file uploads, stream video content, implement server-sent events, and create real-time chat systems using FastAPI.

## 🎯 What You'll Learn

- Streaming responses for large data sets
- File upload with progress tracking
- Server-sent events for real-time updates
- WebSocket connections for live features
- Video/audio streaming fundamentals

## 🎬 Meet StreamVerse Platform

Our streaming platform demonstrates real-time capabilities through:

**Key Features:**
- 🎥 Live video streaming and broadcasting
- 💬 Real-time chat during streams
- 📊 Live viewer analytics and engagement
- 📁 Progressive file upload with progress bars
- 🔔 Instant notifications and alerts

## 🚀 Core Streaming Concepts

### **1. Streaming Large Responses**

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI(title="🎬 StreamVerse Platform")

async def generate_live_comments():
    """Stream live comments as they arrive"""
    comments = [
        {"user": "gamer123", "text": "Amazing stream! 🔥", "timestamp": "2024-01-15T10:30:00"},
        {"user": "streamer_fan", "text": "Love this content!", "timestamp": "2024-01-15T10:30:05"},
        {"user": "chat_master", "text": "First time watching, subscribed!", "timestamp": "2024-01-15T10:30:10"}
    ]
    
    for comment in comments:
        yield f"data: {json.dumps(comment)}\n\n"
        await asyncio.sleep(1)  # Simulate real-time delay

@app.get("/streams/{stream_id}/comments/live")
async def stream_live_comments(stream_id: str):
    """Stream live comments for a specific stream"""
    return StreamingResponse(
        generate_live_comments(),
        media_type="text/plain"
    )
```

### **2. File Upload with Progress**

```python
from fastapi import File, UploadFile, Form
from fastapi.responses import JSONResponse
import aiofiles
import os

@app.post("/streams/upload-video/")
async def upload_video_stream(
    file: UploadFile = File(..., description="Video file to upload"),
    title: str = Form(..., description="Video title"),
    description: str = Form("", description="Video description")
):
    """Upload video file with streaming support"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Only video files allowed")
    
    file_path = f"uploads/videos/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Stream file to disk in chunks
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)
    
    return {
        "message": "Video uploaded successfully",
        "filename": file.filename,
        "title": title,
        "file_size": file.size,
        "file_path": file_path
    }

@app.post("/streams/upload-with-progress/")
async def upload_with_progress(file: UploadFile = File(...)):
    """Upload file with progress tracking"""
    
    file_id = f"upload_{uuid.uuid4().hex[:8]}"
    file_path = f"uploads/{file_id}_{file.filename}"
    
    total_size = file.size
    uploaded_size = 0
    
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            await f.write(chunk)
            uploaded_size += len(chunk)
            
            # You could emit progress here via WebSocket
            progress = (uploaded_size / total_size) * 100
            await broadcast_progress(file_id, progress)
    
    return {"file_id": file_id, "status": "completed", "progress": 100}
```

### **3. Server-Sent Events (SSE)**

```python
import asyncio
import json
from datetime import datetime

async def generate_stream_analytics(stream_id: str):
    """Generate real-time stream analytics"""
    while True:
        analytics = {
            "stream_id": stream_id,
            "viewer_count": random.randint(50, 1000),
            "likes": random.randint(100, 500),
            "comments_per_minute": random.randint(10, 50),
            "timestamp": datetime.now().isoformat()
        }
        
        yield f"data: {json.dumps(analytics)}\n\n"
        await asyncio.sleep(2)  # Update every 2 seconds

@app.get("/streams/{stream_id}/analytics/live")
async def stream_analytics(stream_id: str):
    """Real-time stream analytics via SSE"""
    return StreamingResponse(
        generate_stream_analytics(stream_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

## 🔗 WebSocket Live Features

### **1. Real-time Chat System**

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class StreamChatManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.moderators: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str, user_id: str):
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = set()
        self.active_connections[stream_id].add(websocket)
        
        # Welcome message
        await websocket.send_json({
            "type": "system",
            "message": f"Welcome to the stream chat!",
            "user_count": len(self.active_connections[stream_id])
        })

    async def disconnect(self, websocket: WebSocket, stream_id: str):
        if stream_id in self.active_connections:
            self.active_connections[stream_id].discard(websocket)

    async def broadcast_to_stream(self, message: dict, stream_id: str):
        if stream_id in self.active_connections:
            for connection in self.active_connections[stream_id].copy():
                try:
                    await connection.send_json(message)
                except:
                    await self.disconnect(connection, stream_id)

chat_manager = StreamChatManager()

@app.websocket("/streams/{stream_id}/chat")
async def stream_chat(websocket: WebSocket, stream_id: str, user_id: str):
    await chat_manager.connect(websocket, stream_id, user_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Process chat message
            message = {
                "type": "chat",
                "user_id": user_id,
                "message": data["message"],
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all viewers
            await chat_manager.broadcast_to_stream(message, stream_id)
            
    except WebSocketDisconnect:
        await chat_manager.disconnect(websocket, stream_id)
```

### **2. Live Stream Broadcasting**

```python
@app.websocket("/streams/{stream_id}/broadcast")
async def stream_broadcast(websocket: WebSocket, stream_id: str, broadcaster_id: str):
    """WebSocket endpoint for broadcasters to send live data"""
    await websocket.accept()
    
    try:
        while True:
            stream_data = await websocket.receive_json()
            
            # Process stream data (video frames, audio, etc.)
            processed_data = {
                "stream_id": stream_id,
                "broadcaster": broadcaster_id,
                "data": stream_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all viewers
            await broadcast_to_viewers(stream_id, processed_data)
            
    except WebSocketDisconnect:
        await handle_broadcaster_disconnect(stream_id, broadcaster_id)
```

## 📊 Advanced Streaming Patterns

### **1. Chunked Data Processing**

```python
@app.post("/analytics/process-logs/")
async def process_large_log_file(file: UploadFile = File(...)):
    """Process large log files in chunks"""
    
    async def process_log_chunks():
        line_count = 0
        error_count = 0
        
        async for line in file.stream():
            line_count += 1
            line_text = line.decode('utf-8').strip()
            
            if "ERROR" in line_text:
                error_count += 1
            
            # Yield progress every 1000 lines
            if line_count % 1000 == 0:
                yield f"data: {json.dumps({'processed': line_count, 'errors': error_count})}\n\n"
                await asyncio.sleep(0.01)  # Prevent blocking
        
        # Final result
        yield f"data: {json.dumps({'completed': True, 'total_lines': line_count, 'total_errors': error_count})}\n\n"
    
    return StreamingResponse(
        process_log_chunks(),
        media_type="text/event-stream"
    )
```

### **2. Real-time Data Aggregation**

```python
@app.get("/streams/global-stats/live")
async def global_stream_stats():
    """Live aggregation of all platform statistics"""
    
    async def generate_global_stats():
        while True:
            stats = {
                "total_active_streams": await count_active_streams(),
                "total_viewers": await count_total_viewers(),
                "popular_categories": await get_popular_categories(),
                "trending_streams": await get_trending_streams(),
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(stats)}\n\n"
            await asyncio.sleep(5)  # Update every 5 seconds
    
    return StreamingResponse(
        generate_global_stats(),
        media_type="text/event-stream"
    )
```

## 🎮 Key Streaming Endpoints

### **Content Management**
```python
@app.post("/streams/create", response_model=StreamResponse)
async def create_stream(stream_data: StreamCreate)

@app.get("/streams/{stream_id}")
async def get_stream_details(stream_id: str)

@app.put("/streams/{stream_id}/status")
async def update_stream_status(stream_id: str, status: StreamStatus)
```

### **Real-time Features**
```python
@app.websocket("/streams/{stream_id}/chat")
async def stream_chat(websocket: WebSocket, stream_id: str)

@app.get("/streams/{stream_id}/analytics/live")
async def stream_analytics(stream_id: str)

@app.post("/streams/upload-video/")
async def upload_video_stream(file: UploadFile = File(...))
```

## 🛠️ Running StreamVerse

```bash
cd 08-streaming
uvicorn main:app --reload

# Test streaming endpoints:
# SSE: http://localhost:8000/streams/demo/analytics/live
# WebSocket: ws://localhost:8000/streams/demo/chat
# Upload: POST /streams/upload-video/
```

## 📊 Streaming Performance

| Feature | Traditional | Streaming | Benefit |
|---------|-------------|-----------|---------|
| **Large File Upload** | 30s timeout | Progressive | No timeouts |
| **Live Data** | Polling every 5s | Real-time SSE | Instant updates |
| **Chat Messages** | HTTP requests | WebSocket | 10x faster |
| **Memory Usage** | Load entire file | Process chunks | 90% less memory |

## 🎮 Practice Exercises

1. **📺 Live Streaming**: Build WebRTC integration for video streams
2. **📊 Analytics Dashboard**: Create real-time metrics with SSE
3. **💬 Moderation Tools**: Add chat filtering and moderation
4. **🔔 Notifications**: Implement real-time notification system

## 💡 Streaming Best Practices

### **Performance Tips**
- Use appropriate chunk sizes (1MB for files, 8KB for real-time)
- Implement connection cleanup and error handling
- Add rate limiting for WebSocket connections
- Use Redis for scaling WebSocket across multiple servers

### **User Experience**
- Show upload progress for large files
- Provide fallbacks for connection issues
- Implement reconnection logic for WebSockets
- Cache frequently accessed streaming data

## 🚀 What's Next?

In **Section 9: Security**, we'll build a secure banking platform that shows how to implement enterprise-grade authentication, authorization, and data protection!

**Key Takeaway**: Streaming enables real-time, responsive applications that handle large data efficiently and provide instant user feedback! 🎬⚡ 