import asyncio
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException, Query, Path, Depends, File, UploadFile
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field
from enum import Enum
import random

# Initialize our Live Content Streaming Platform
app = FastAPI(
    title="🎬 StreamVerse - Live Content Streaming Platform",
    description="""
    Welcome to **StreamVerse** - where entertainment comes alive! 📺✨
    
    Experience the future of content streaming with:
    
    * 🎥 **Live Video Streaming**: Real-time video content delivery
    * 📊 **Live Analytics**: Real-time viewer statistics and engagement metrics
    * 💬 **Live Chat**: Instant interaction between streamers and viewers
    * 🎵 **Audio Streaming**: High-quality music and podcast streaming
    * 📱 **Real-time Notifications**: Instant updates via Server-Sent Events
    * 🎮 **Interactive Features**: Polls, reactions, and viewer participation
    * 📈 **Live Dashboards**: Real-time performance monitoring
    
    Built with FastAPI's streaming superpowers - delivering content to millions! 🌍
    """,
    version="1.0.0"
)

# === STREAMING MODELS ===

class StreamType(str, Enum):
    LIVE_VIDEO = "live_video"
    VOD = "video_on_demand"
    AUDIO = "audio"
    PODCAST = "podcast"
    GAMING = "gaming"
    EDUCATIONAL = "educational"

class StreamQuality(str, Enum):
    LOW_240P = "240p"
    MEDIUM_480P = "480p"
    HIGH_720P = "720p"
    FULL_HD_1080P = "1080p"
    ULTRA_HD_4K = "4k"

class ViewerAction(str, Enum):
    JOIN = "join"
    LEAVE = "leave"
    LIKE = "like"
    FOLLOW = "follow"
    SHARE = "share"
    COMMENT = "comment"

class Stream(BaseModel):
    id: str = Field(..., description="Unique stream identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Stream title")
    description: Optional[str] = Field(None, max_length=1000)
    streamer_name: str = Field(..., description="Content creator name")
    stream_type: StreamType = Field(..., description="Type of content")
    is_live: bool = Field(True, description="Whether stream is currently live")
    viewer_count: int = Field(0, ge=0, description="Current viewer count")
    quality: StreamQuality = Field(StreamQuality.HIGH_720P, description="Stream quality")
    started_at: datetime = Field(default_factory=datetime.now)
    thumbnail_url: Optional[str] = None
    tags: List[str] = []

class ChatMessage(BaseModel):
    id: str
    username: str
    message: str
    timestamp: datetime
    stream_id: str
    is_moderator: bool = False
    emotes: List[str] = []

class ViewerStats(BaseModel):
    stream_id: str
    current_viewers: int
    peak_viewers: int
    total_views: int
    average_watch_time: float
    engagement_rate: float
    top_countries: List[Dict[str, int]]
    viewer_retention: List[Dict[str, float]]

# === GLOBAL STATE MANAGEMENT ===

# In-memory storage (use Redis in production)
active_streams: Dict[str, Stream] = {}
stream_viewers: Dict[str, set] = {}  # stream_id -> set of viewer_ids
live_chat: Dict[str, List[ChatMessage]] = {}  # stream_id -> messages
viewer_analytics: Dict[str, ViewerStats] = {}

# WebSocket connection managers
class StreamConnectionManager:
    def __init__(self):
        self.stream_connections: Dict[str, List[WebSocket]] = {}  # stream_id -> websockets
        self.chat_connections: Dict[str, List[WebSocket]] = {}   # stream_id -> chat websockets
    
    async def connect_to_stream(self, websocket: WebSocket, stream_id: str):
        await websocket.accept()
        if stream_id not in self.stream_connections:
            self.stream_connections[stream_id] = []
        self.stream_connections[stream_id].append(websocket)
    
    def disconnect_from_stream(self, websocket: WebSocket, stream_id: str):
        if stream_id in self.stream_connections:
            if websocket in self.stream_connections[stream_id]:
                self.stream_connections[stream_id].remove(websocket)
    
    async def broadcast_to_stream_viewers(self, stream_id: str, message: str):
        if stream_id in self.stream_connections:
            disconnected = []
            for websocket in self.stream_connections[stream_id]:
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect_from_stream(ws, stream_id)

stream_manager = StreamConnectionManager()

# === STREAMING ENDPOINTS ===

@app.get("/")
def streaming_platform_home():
    """🏠 Welcome to StreamVerse - Where Entertainment Lives!"""
    return {
        "message": "🎬 Welcome to StreamVerse!",
        "tagline": "Where every moment becomes content, and every viewer becomes part of the story ✨",
        "platform_stats": {
            "live_streams": len([s for s in active_streams.values() if s.is_live]),
            "total_viewers": sum(s.viewer_count for s in active_streams.values()),
            "content_hours": 145000,
            "creators": 25000
        },
        "trending_categories": ["🎮 Gaming", "🎵 Music", "📚 Education", "🍳 Cooking", "🏋️ Fitness"],
        "featured_streams": [
            {"title": "Epic Gaming Marathon", "streamer": "ProGamer2024", "viewers": 15420},
            {"title": "Cooking with AI", "streamer": "ChefTechie", "viewers": 8750},
            {"title": "Live Music Session", "streamer": "MelodyMaker", "viewers": 12380}
        ]
    }

# === LIVE STREAM MANAGEMENT ===

@app.post("/streams/", response_model=Stream)
async def create_live_stream(
    title: str = Query(..., min_length=1, max_length=200),
    description: Optional[str] = Query(None, max_length=1000),
    streamer_name: str = Query(..., min_length=1, max_length=50),
    stream_type: StreamType = Query(StreamType.LIVE_VIDEO),
    quality: StreamQuality = Query(StreamQuality.HIGH_720P),
    tags: str = Query("", description="Comma-separated tags"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    🎥 Go Live! Start your streaming adventure!
    
    Create a live stream and start broadcasting to the world.
    """
    stream_id = f"stream_{uuid.uuid4().hex[:12]}"
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    new_stream = Stream(
        id=stream_id,
        title=title,
        description=description,
        streamer_name=streamer_name,
        stream_type=stream_type,
        quality=quality,
        tags=tag_list,
        thumbnail_url=f"https://thumbnails.streamverse.com/{stream_id}.jpg"
    )
    
    # Store stream
    active_streams[stream_id] = new_stream
    stream_viewers[stream_id] = set()
    live_chat[stream_id] = []
    
    # Initialize analytics
    viewer_analytics[stream_id] = ViewerStats(
        stream_id=stream_id,
        current_viewers=0,
        peak_viewers=0,
        total_views=0,
        average_watch_time=0.0,
        engagement_rate=0.0,
        top_countries=[],
        viewer_retention=[]
    )
    
    # Start background analytics tracking
    background_tasks.add_task(track_stream_analytics, stream_id)
    
    return new_stream

@app.get("/streams/", response_model=List[Stream])
async def discover_live_streams(
    stream_type: Optional[StreamType] = Query(None, description="Filter by content type"),
    min_viewers: int = Query(0, ge=0, description="Minimum viewer count"),
    live_only: bool = Query(True, description="Show only live streams"),
    limit: int = Query(20, ge=1, le=100, description="Max streams to return")
):
    """
    🔍 Discover amazing live content!
    
    Browse through our incredible collection of live streams and find your next binge-watch.
    """
    filtered_streams = []
    
    for stream in active_streams.values():
        if live_only and not stream.is_live:
            continue
        if stream_type and stream.stream_type != stream_type:
            continue
        if stream.viewer_count < min_viewers:
            continue
        filtered_streams.append(stream)
    
    # Sort by viewer count (most popular first)
    filtered_streams.sort(key=lambda s: s.viewer_count, reverse=True)
    
    return filtered_streams[:limit]

@app.get("/streams/{stream_id}", response_model=Stream)
async def get_stream_details(stream_id: str):
    """📺 Get detailed information about a specific stream"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="🔍 Stream not found! It might have ended or moved to another dimension!")
    
    return active_streams[stream_id]

# === REAL-TIME VIDEO STREAMING ===

@app.get("/stream/video/{stream_id}")
async def stream_video_content(
    stream_id: str = Path(..., description="Stream ID to watch"),
    quality: StreamQuality = Query(StreamQuality.HIGH_720P, description="Preferred video quality")
):
    """
    🎥 Stream live video content!
    
    Get real-time video stream with adaptive quality based on connection.
    """
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found!")
    
    stream = active_streams[stream_id]
    if not stream.is_live:
        raise HTTPException(status_code=410, detail="This stream has ended!")
    
    async def generate_video_chunks():
        """Simulate video streaming with metadata"""
        chunk_number = 0
        while stream_id in active_streams and active_streams[stream_id].is_live:
            # Simulate video chunk data (in real app, this would be actual video data)
            chunk_data = {
                "chunk_id": chunk_number,
                "timestamp": datetime.now().isoformat(),
                "quality": quality.value,
                "duration_ms": 2000,  # 2-second chunks
                "data_size_kb": random.randint(50, 200),
                "video_url": f"https://video-cdn.streamverse.com/{stream_id}/chunk_{chunk_number}_{quality.value}.ts"
            }
            
            yield f"data: {json.dumps(chunk_data)}\n\n"
            chunk_number += 1
            
            # Wait for next chunk (2 seconds for live streaming)
            await asyncio.sleep(2)
    
    return StreamingResponse(
        generate_video_chunks(),
        media_type="text/stream-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Stream-Type": "live-video"
        }
    )

# === LIVE AUDIO STREAMING ===

@app.get("/stream/audio/{stream_id}")
async def stream_audio_content(stream_id: str):
    """
    🎵 Stream high-quality audio content!
    
    Perfect for music streams, podcasts, and audio-only content.
    """
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Audio stream not found!")
    
    async def generate_audio_stream():
        """Generate continuous audio stream chunks"""
        while stream_id in active_streams:
            # Simulate audio chunk (in real app, this would be actual audio data)
            audio_chunk = {
                "timestamp": time.time(),
                "sample_rate": 44100,
                "bitrate": 320,  # 320 kbps
                "format": "mp3",
                "chunk_size": 4096,
                "audio_data": f"https://audio-cdn.streamverse.com/{stream_id}/audio_{int(time.time())}.mp3"
            }
            
            yield f"data: {json.dumps(audio_chunk)}\n\n"
            await asyncio.sleep(0.1)  # 100ms audio chunks
    
    return StreamingResponse(
        generate_audio_stream(),
        media_type="text/stream-stream",
        headers={
            "X-Content-Type": "audio/mpeg",
            "X-Stream-Type": "live-audio"
        }
    )

# === REAL-TIME ANALYTICS STREAMING ===

@app.get("/stream/analytics/{stream_id}")
async def stream_live_analytics(stream_id: str):
    """
    📊 Real-time streaming analytics!
    
    Get live viewer statistics, engagement metrics, and performance data.
    """
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found!")
    
    async def generate_analytics_stream():
        """Stream real-time analytics data"""
        while stream_id in active_streams:
            current_time = datetime.now()
            
            # Generate realistic analytics data
            analytics_data = {
                "timestamp": current_time.isoformat(),
                "stream_id": stream_id,
                "viewers": {
                    "current": len(stream_viewers.get(stream_id, set())),
                    "peak": max(50, len(stream_viewers.get(stream_id, set())) + random.randint(-10, 30)),
                    "total_unique": random.randint(100, 5000)
                },
                "engagement": {
                    "chat_messages_per_minute": random.randint(5, 150),
                    "likes_per_minute": random.randint(10, 200),
                    "shares_this_hour": random.randint(1, 50),
                    "average_watch_time": round(random.uniform(2.5, 45.0), 1)
                },
                "technical": {
                    "bitrate_mbps": round(random.uniform(2.5, 8.0), 1),
                    "frames_dropped": random.randint(0, 5),
                    "latency_ms": random.randint(500, 3000),
                    "quality_score": round(random.uniform(85.0, 99.5), 1)
                },
                "geographic": {
                    "top_countries": [
                        {"country": "United States", "percentage": 35.2},
                        {"country": "United Kingdom", "percentage": 18.7},
                        {"country": "Canada", "percentage": 12.3},
                        {"country": "Germany", "percentage": 8.9},
                        {"country": "Australia", "percentage": 6.4}
                    ]
                },
                "trending": {
                    "is_trending": random.choice([True, False]),
                    "trend_score": round(random.uniform(0.1, 10.0), 1),
                    "category_rank": random.randint(1, 50)
                }
            }
            
            yield f"data: {json.dumps(analytics_data)}\n\n"
            await asyncio.sleep(5)  # Update every 5 seconds
    
    return StreamingResponse(
        generate_analytics_stream(),
        media_type="text/stream-stream",
        headers={"X-Analytics-Version": "v2.1"}
    )

# === LIVE CHAT WEBSOCKET ===

@app.websocket("/ws/chat/{stream_id}/{username}")
async def live_chat_websocket(websocket: WebSocket, stream_id: str, username: str):
    """
    💬 Join the live chat conversation!
    
    Real-time chat during live streams with instant message delivery.
    """
    await websocket.accept()
    
    # Add user to chat
    if stream_id not in live_chat:
        live_chat[stream_id] = []
    
    try:
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": f"🎉 {username} joined the chat!",
            "timestamp": datetime.now().isoformat(),
            "viewer_count": len(stream_viewers.get(stream_id, set()))
        }
        await websocket.send_text(json.dumps(welcome_msg))
        
        # Add to stream viewers
        if stream_id not in stream_viewers:
            stream_viewers[stream_id] = set()
        stream_viewers[stream_id].add(username)
        
        # Update viewer count
        if stream_id in active_streams:
            active_streams[stream_id].viewer_count = len(stream_viewers[stream_id])
        
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Create chat message
            chat_message = ChatMessage(
                id=str(uuid.uuid4()),
                username=username,
                message=message_data.get("message", ""),
                timestamp=datetime.now(),
                stream_id=stream_id,
                emotes=message_data.get("emotes", [])
            )
            
            # Store message
            live_chat[stream_id].append(chat_message)
            
            # Broadcast to all viewers in this stream
            broadcast_data = {
                "type": "chat_message",
                "id": chat_message.id,
                "username": chat_message.username,
                "message": chat_message.message,
                "timestamp": chat_message.timestamp.isoformat(),
                "emotes": chat_message.emotes,
                "is_moderator": chat_message.is_moderator
            }
            
            await stream_manager.broadcast_to_stream_viewers(
                stream_id, 
                json.dumps(broadcast_data)
            )
            
    except WebSocketDisconnect:
        # Remove user from viewers
        if stream_id in stream_viewers and username in stream_viewers[stream_id]:
            stream_viewers[stream_id].remove(username)
            
            # Update viewer count
            if stream_id in active_streams:
                active_streams[stream_id].viewer_count = len(stream_viewers[stream_id])
            
            # Broadcast leave message
            leave_msg = {
                "type": "system",
                "message": f"👋 {username} left the chat",
                "timestamp": datetime.now().isoformat(),
                "viewer_count": len(stream_viewers[stream_id])
            }
            
            await stream_manager.broadcast_to_stream_viewers(
                stream_id, 
                json.dumps(leave_msg)
            )

# === SERVER-SENT EVENTS FOR NOTIFICATIONS ===

@app.get("/notifications/live")
async def live_notifications():
    """
    🔔 Real-time platform notifications!
    
    Get instant updates about new streams, trending content, and platform events.
    """
    async def generate_notifications():
        """Generate real-time platform notifications"""
        notification_types = [
            "new_stream_started",
            "stream_going_viral", 
            "creator_milestone",
            "trending_content",
            "platform_update",
            "community_event"
        ]
        
        while True:
            notification_type = random.choice(notification_types)
            
            notifications = {
                "new_stream_started": {
                    "type": "new_stream",
                    "title": "🎥 New Stream Alert!",
                    "message": f"TechGuru just went live with 'Building AI with Python'",
                    "action_url": "/streams/stream_abc123",
                    "priority": "normal"
                },
                "stream_going_viral": {
                    "type": "trending",
                    "title": "🔥 Stream Going Viral!",
                    "message": "Epic Gaming Marathon just hit 50K viewers!",
                    "action_url": "/streams/stream_def456", 
                    "priority": "high"
                },
                "creator_milestone": {
                    "type": "milestone",
                    "title": "🎉 Creator Milestone!",
                    "message": "MelodyMaker just reached 100K followers!",
                    "action_url": "/creators/melody_maker",
                    "priority": "normal"
                },
                "trending_content": {
                    "type": "discovery",
                    "title": "📈 Trending Now!",
                    "message": "AI & Technology streams are trending today",
                    "action_url": "/discover?category=tech",
                    "priority": "low"
                },
                "platform_update": {
                    "type": "update",
                    "title": "✨ New Feature!",
                    "message": "Introducing 4K streaming for Pro users!",
                    "action_url": "/features/4k-streaming",
                    "priority": "normal"
                },
                "community_event": {
                    "type": "event",
                    "title": "🎪 Community Event!",
                    "message": "Join the StreamVerse Creator Summit this weekend",
                    "action_url": "/events/creator-summit",
                    "priority": "high"
                }
            }
            
            notification = notifications[notification_type]
            notification["id"] = str(uuid.uuid4())
            notification["timestamp"] = datetime.now().isoformat()
            
            yield f"data: {json.dumps(notification)}\n\n"
            
            # Random interval between 10-30 seconds
            await asyncio.sleep(random.randint(10, 30))
    
    return StreamingResponse(
        generate_notifications(),
        media_type="text/stream-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Notification-Version": "v1.0"
        }
    )

# === FILE UPLOAD STREAMING ===

@app.post("/upload/video/")
async def upload_video_stream(
    file: UploadFile = File(..., description="Video file to upload"),
    title: str = Query(..., description="Video title"),
    description: Optional[str] = Query(None, description="Video description")
):
    """
    📤 Upload video content with real-time progress!
    
    Stream video uploads with live progress tracking and processing updates.
    """
    
    async def process_upload_with_progress():
        """Process file upload with streaming progress updates"""
        
        # Initial upload start
        yield f"data: {json.dumps({'status': 'started', 'message': '📤 Upload initiated...', 'progress': 0})}\n\n"
        
        # Simulate file processing stages
        stages = [
            {"name": "Reading file", "duration": 2},
            {"name": "Validating format", "duration": 1},
            {"name": "Processing video", "duration": 5},
            {"name": "Generating thumbnails", "duration": 2},
            {"name": "Creating quality variants", "duration": 4},
            {"name": "Uploading to CDN", "duration": 3},
            {"name": "Finalizing", "duration": 1}
        ]
        
        total_duration = sum(stage["duration"] for stage in stages)
        elapsed = 0
        
        for i, stage in enumerate(stages):
            # Stage start
            stage_progress = (elapsed / total_duration) * 100
            yield f"data: {json.dumps({'status': 'processing', 'stage': stage['name'], 'progress': round(stage_progress), 'message': f'⚙️ {stage[\"name\"]}...'})}\n\n"
            
            # Simulate stage processing with incremental updates
            stage_steps = stage["duration"] * 2  # 2 updates per second
            for step in range(stage_steps):
                await asyncio.sleep(0.5)
                step_progress = ((elapsed + (step + 1) * 0.5) / total_duration) * 100
                yield f"data: {json.dumps({'status': 'processing', 'stage': stage['name'], 'progress': round(step_progress, 1)})}\n\n"
            
            elapsed += stage["duration"]
        
        # Upload complete
        video_id = f"video_{uuid.uuid4().hex[:12]}"
        completion_data = {
            "status": "completed",
            "message": "🎉 Video uploaded successfully!",
            "progress": 100,
            "video_id": video_id,
            "video_url": f"https://videos.streamverse.com/{video_id}",
            "thumbnail_url": f"https://thumbnails.streamverse.com/{video_id}.jpg",
            "processing_time": f"{total_duration} seconds"
        }
        
        yield f"data: {json.dumps(completion_data)}\n\n"
    
    return StreamingResponse(
        process_upload_with_progress(),
        media_type="text/stream-stream",
        headers={"X-Upload-Session": str(uuid.uuid4())}
    )

# === REAL-TIME DASHBOARD STREAMING ===

@app.get("/dashboard/live")
async def live_platform_dashboard():
    """
    📊 Real-time platform dashboard!
    
    Monitor platform performance, user activity, and content statistics in real-time.
    """
    async def generate_dashboard_data():
        """Stream comprehensive platform metrics"""
        
        while True:
            current_time = datetime.now()
            
            dashboard_data = {
                "timestamp": current_time.isoformat(),
                "platform_metrics": {
                    "total_streams": len(active_streams),
                    "live_streams": len([s for s in active_streams.values() if s.is_live]),
                    "total_viewers": sum(len(viewers) for viewers in stream_viewers.values()),
                    "total_creators": random.randint(24000, 26000),
                    "content_hours_today": random.randint(12000, 15000)
                },
                "real_time_activity": {
                    "new_streams_last_hour": random.randint(150, 300),
                    "chat_messages_per_second": random.randint(500, 2000),
                    "concurrent_uploads": random.randint(50, 150),
                    "active_moderations": random.randint(10, 50)
                },
                "performance_metrics": {
                    "avg_latency_ms": random.randint(200, 800),
                    "server_load_percent": random.randint(45, 85),
                    "cdn_hit_rate_percent": round(random.uniform(92.0, 99.5), 1),
                    "uptime_percent": round(random.uniform(99.8, 99.99), 2)
                },
                "content_trends": {
                    "top_categories": [
                        {"name": "Gaming", "streams": random.randint(800, 1200), "growth": "+15%"},
                        {"name": "Music", "streams": random.randint(400, 800), "growth": "+8%"},
                        {"name": "Education", "streams": random.randint(300, 600), "growth": "+22%"},
                        {"name": "Tech", "streams": random.randint(200, 400), "growth": "+12%"}
                    ],
                    "viral_content": [
                        {"title": "AI Coding Marathon", "views": random.randint(50000, 100000)},
                        {"title": "Live Music Concert", "views": random.randint(75000, 150000)}
                    ]
                },
                "revenue_metrics": {
                    "revenue_today": random.randint(45000, 75000),
                    "subscription_signups": random.randint(500, 1500),
                    "creator_earnings": random.randint(25000, 45000),
                    "platform_commission": random.randint(8000, 15000)
                }
            }
            
            yield f"data: {json.dumps(dashboard_data)}\n\n"
            await asyncio.sleep(3)  # Update every 3 seconds
    
    return StreamingResponse(
        generate_dashboard_data(),
        media_type="text/stream-stream",
        headers={"X-Dashboard-Version": "v2.0"}
    )

# === BACKGROUND TASKS FOR ANALYTICS ===

async def track_stream_analytics(stream_id: str):
    """Background task to track and update stream analytics"""
    while stream_id in active_streams:
        # Update analytics data
        current_viewers = len(stream_viewers.get(stream_id, set()))
        
        if stream_id in viewer_analytics:
            analytics = viewer_analytics[stream_id]
            analytics.current_viewers = current_viewers
            analytics.peak_viewers = max(analytics.peak_viewers, current_viewers)
            analytics.total_views += random.randint(0, 10)  # Simulate new viewers
        
        await asyncio.sleep(10)  # Update every 10 seconds

# === DEMO PAGES ===

@app.get("/demo/streaming", response_class=HTMLResponse)
def streaming_demo_page():
    """🎬 Interactive streaming demo page"""
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>StreamVerse - Live Streaming Demo</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #1a1a1a; color: white; }
                .container { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
                .video-player { background: #000; border-radius: 8px; padding: 20px; text-align: center; height: 400px; }
                .chat-section { background: #2a2a2a; border-radius: 8px; padding: 20px; }
                .analytics { background: #333; border-radius: 8px; padding: 15px; margin-top: 20px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; background: #4a4a4a; border-radius: 5px; }
                #chat-messages { height: 300px; overflow-y: auto; border: 1px solid #555; padding: 10px; margin-bottom: 10px; }
                .message { margin: 5px 0; }
                .system { color: #ffd700; font-style: italic; }
                .user { color: #87ceeb; }
                button { background: #ff6b6b; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
                button:hover { background: #ff5252; }
                input { width: 80%; padding: 10px; margin-right: 10px; }
            </style>
        </head>
        <body>
            <h1>🎬 StreamVerse Live Demo</h1>
            
            <div class="container">
                <div class="video-player">
                    <h2>🎥 Live Stream Player</h2>
                    <div style="background: #444; height: 250px; border-radius: 5px; display: flex; align-items: center; justify-content: center;">
                        <div id="video-status">📺 Click "Start Streaming" to begin</div>
                    </div>
                    <div style="margin-top: 20px;">
                        <button onclick="startStream()">🎥 Start Streaming</button>
                        <button onclick="stopStream()">⏹️ Stop Stream</button>
                        <button onclick="toggleQuality()">⚙️ Toggle Quality</button>
                    </div>
                </div>
                
                <div class="chat-section">
                    <h3>💬 Live Chat</h3>
                    <div id="chat-messages"></div>
                    <div>
                        <input type="text" id="message-input" placeholder="Type your message..." onkeypress="handleEnter(event)">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <div class="analytics">
                <h3>📊 Live Analytics</h3>
                <div id="analytics-data">
                    <div class="metric">👥 Viewers: <span id="viewer-count">0</span></div>
                    <div class="metric">💬 Chat/min: <span id="chat-rate">0</span></div>
                    <div class="metric">🔥 Engagement: <span id="engagement">0%</span></div>
                    <div class="metric">⚡ Latency: <span id="latency">0ms</span></div>
                </div>
            </div>
            
            <div style="margin-top: 20px; padding: 20px; background: #2a2a2a; border-radius: 8px;">
                <h3>🚀 Real-time Features</h3>
                <button onclick="connectNotifications()">🔔 Connect Notifications</button>
                <button onclick="openAnalytics()">📈 Live Analytics</button>
                <button onclick="testUpload()">📤 Test Upload</button>
                <div id="features-output" style="margin-top: 10px; padding: 10px; background: #1a1a1a; border-radius: 5px; min-height: 100px;"></div>
            </div>
            
            <script>
                let streamId = 'demo_stream_' + Math.random().toString(36).substr(2, 9);
                let username = 'User_' + Math.random().toString(36).substr(2, 5);
                let chatSocket = null;
                let notificationSource = null;
                let analyticsSource = null;
                
                function startStream() {
                    document.getElementById('video-status').innerHTML = '🔴 LIVE - Streaming in 720p';
                    connectChat();
                    startAnalytics();
                }
                
                function stopStream() {
                    document.getElementById('video-status').innerHTML = '⚫ Stream Ended';
                    if (chatSocket) chatSocket.close();
                    if (analyticsSource) analyticsSource.close();
                }
                
                function connectChat() {
                    const wsUrl = `ws://localhost:8000/ws/chat/${streamId}/${username}`;
                    chatSocket = new WebSocket(wsUrl);
                    
                    chatSocket.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        const chatDiv = document.getElementById('chat-messages');
                        
                        let messageClass = data.type === 'system' ? 'system' : 'user';
                        chatDiv.innerHTML += `<div class="message ${messageClass}">
                            ${data.type === 'system' ? data.message : `<strong>${data.username}:</strong> ${data.message}`}
                        </div>`;
                        chatDiv.scrollTop = chatDiv.scrollHeight;
                    };
                }
                
                function sendMessage() {
                    const input = document.getElementById('message-input');
                    if (input.value && chatSocket) {
                        chatSocket.send(JSON.stringify({message: input.value}));
                        input.value = '';
                    }
                }
                
                function handleEnter(event) {
                    if (event.key === 'Enter') sendMessage();
                }
                
                function startAnalytics() {
                    analyticsSource = new EventSource(`/stream/analytics/${streamId}`);
                    analyticsSource.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        document.getElementById('viewer-count').textContent = data.viewers.current;
                        document.getElementById('chat-rate').textContent = data.engagement.chat_messages_per_minute;
                        document.getElementById('engagement').textContent = data.engagement.engagement_rate || '95%';
                        document.getElementById('latency').textContent = data.technical.latency_ms;
                    };
                }
                
                function connectNotifications() {
                    const output = document.getElementById('features-output');
                    output.innerHTML = '🔔 Connecting to live notifications...<br>';
                    
                    const notificationSource = new EventSource('/notifications/live');
                    notificationSource.onmessage = function(event) {
                        const notification = JSON.parse(event.data);
                        output.innerHTML += `<div style="margin: 5px 0; padding: 8px; background: #444; border-radius: 3px;">
                            <strong>${notification.title}</strong><br>
                            ${notification.message}
                        </div>`;
                    };
                }
                
                function openAnalytics() {
                    window.open('/stream/analytics/' + streamId, '_blank');
                }
                
                function testUpload() {
                    const output = document.getElementById('features-output');
                    output.innerHTML = '📤 Starting upload demo...<br>';
                    
                    // Simulate upload progress
                    fetch('/upload/video/?title=Demo Video&description=Test upload', {
                        method: 'POST',
                        body: new FormData()
                    }).then(response => {
                        if (response.body) {
                            const reader = response.body.getReader();
                            function readStream() {
                                reader.read().then(({done, value}) => {
                                    if (!done) {
                                        const text = new TextDecoder().decode(value);
                                        output.innerHTML += text.replace(/data: /g, '').replace(/\\n\\n/g, '<br>');
                                        readStream();
                                    }
                                });
                            }
                            readStream();
                        }
                    });
                }
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    print("🎬 Starting StreamVerse Platform...")
    print("✨ Where entertainment comes alive!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 