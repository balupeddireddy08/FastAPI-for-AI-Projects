# 🎮 Section 7: Async Programming - Epic Real-time Gaming Platform

Master **asynchronous programming** by building a high-performance gaming platform! Learn how to handle thousands of concurrent users, real-time game states, and live multiplayer experiences using FastAPI's async capabilities.

## 🎯 What You'll Learn

- Async/await fundamentals in FastAPI
- Concurrent request handling
- WebSocket connections for real-time features
- Background tasks and job processing
- Database connection pooling and async ORM

## 🎮 Meet Epic Real-time Gaming Platform

Our gaming platform demonstrates async programming through:

**Key Features:**
- ⚔️ Real-time multiplayer battles
- 🏆 Live tournament brackets
- 💬 In-game chat systems  
- 📊 Real-time analytics dashboards
- 🎯 Matchmaking and lobby systems

## 🚀 Core Async Concepts

### **1. Understanding Async/Await**

```python
import asyncio
from fastapi import FastAPI
from typing import List

app = FastAPI(title="🎮 Epic Gaming Platform")

# Synchronous version (blocking)
def sync_get_player_stats(player_id: int):
    time.sleep(1)  # Simulates database call
    return {"player_id": player_id, "level": 25, "wins": 142}

# Asynchronous version (non-blocking)
async def async_get_player_stats(player_id: int):
    await asyncio.sleep(1)  # Simulates async database call
    return {"player_id": player_id, "level": 25, "wins": 142}

@app.get("/players/{player_id}/stats")
async def get_player_stats(player_id: int):
    """Get player statistics asynchronously"""
    stats = await async_get_player_stats(player_id)
    return stats
```

### **2. Concurrent Operations**

```python
import aiohttp
from asyncio import gather

async def fetch_player_data(player_id: int):
    """Simulate fetching player data from external service"""
    await asyncio.sleep(0.5)
    return {"id": player_id, "username": f"Player{player_id}"}

async def fetch_game_history(player_id: int):
    """Simulate fetching game history"""
    await asyncio.sleep(0.3)
    return {"recent_games": [{"game_id": 1, "result": "win"}]}

@app.get("/players/{player_id}/profile")
async def get_player_profile(player_id: int):
    """Get complete player profile by fetching multiple data sources concurrently"""
    
    # Execute both operations concurrently
    player_data, game_history = await gather(
        fetch_player_data(player_id),
        fetch_game_history(player_id)
    )
    
    return {
        "player": player_data,
        "history": game_history,
        "profile_complete": True
    }
```

### **3. Background Tasks**

```python
from fastapi import BackgroundTasks
import logging

async def log_game_result(game_id: str, result: dict):
    """Background task to log game results"""
    await asyncio.sleep(2)  # Simulate processing
    logging.info(f"Game {game_id} result logged: {result}")

async def update_player_rankings():
    """Background task to update player rankings"""
    await asyncio.sleep(5)  # Simulate complex calculation
    logging.info("Player rankings updated")

@app.post("/games/{game_id}/finish")
async def finish_game(
    game_id: str, 
    result: GameResult,
    background_tasks: BackgroundTasks
):
    """Finish a game and trigger background processing"""
    
    # Add background tasks
    background_tasks.add_task(log_game_result, game_id, result.dict())
    background_tasks.add_task(update_player_rankings)
    
    return {
        "message": "Game finished successfully",
        "game_id": game_id,
        "processing": "Results being processed in background"
    }
```

## 🔗 WebSocket for Real-time Features

### **1. Live Game Updates**

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set

class GameConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_room: str):
        await websocket.accept()
        if game_room not in self.active_connections:
            self.active_connections[game_room] = set()
        self.active_connections[game_room].add(websocket)

    async def disconnect(self, websocket: WebSocket, game_room: str):
        self.active_connections[game_room].discard(websocket)

    async def broadcast_to_room(self, message: dict, game_room: str):
        if game_room in self.active_connections:
            for connection in self.active_connections[game_room].copy():
                try:
                    await connection.send_json(message)
                except:
                    await self.disconnect(connection, game_room)

manager = GameConnectionManager()

@app.websocket("/games/{game_room}/live")
async def game_websocket(websocket: WebSocket, game_room: str):
    await manager.connect(websocket, game_room)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Broadcast player action to all players in room
            await manager.broadcast_to_room({
                "type": "player_action",
                "action": data,
                "timestamp": datetime.now().isoformat()
            }, game_room)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, game_room)
```

### **2. Real-time Chat System**

```python
@app.websocket("/chat/{room_id}")
async def chat_websocket(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, f"chat_{room_id}")
    
    try:
        while True:
            message_data = await websocket.receive_json()
            
            # Process message (profanity filter, etc.)
            processed_message = {
                "user": message_data["user"],
                "message": message_data["message"],
                "timestamp": datetime.now().isoformat(),
                "room_id": room_id
            }
            
            # Broadcast to all users in chat room
            await manager.broadcast_to_room(
                processed_message, 
                f"chat_{room_id}"
            )
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, f"chat_{room_id}")
```

## 🗄️ Async Database Operations

### **1. Async Database Connection**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Async database setup
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/gamedb"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/players/{player_id}")
async def get_player(player_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get player data from database asynchronously"""
    result = await db.execute(
        select(Player).where(Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return player
```

### **2. Concurrent Database Queries**

```python
@app.get("/tournaments/{tournament_id}/leaderboard")
async def get_tournament_leaderboard(
    tournament_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get tournament leaderboard with concurrent queries"""
    
    # Execute multiple queries concurrently
    results = await gather(
        db.execute(select(Player).join(TournamentEntry).where(
            TournamentEntry.tournament_id == tournament_id
        ).order_by(TournamentEntry.score.desc())),
        
        db.execute(select(func.count(TournamentEntry.id)).where(
            TournamentEntry.tournament_id == tournament_id
        )),
        
        db.execute(select(Tournament).where(Tournament.id == tournament_id))
    )
    
    players = results[0].scalars().all()
    total_players = results[1].scalar()
    tournament = results[2].scalar_one()
    
    return {
        "tournament": tournament.name,
        "leaderboard": players,
        "total_players": total_players
    }
```

## ⚡ Performance Optimization

### **1. Connection Pooling**

```python
# Configure connection pool for high concurrency
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Number of connections to maintain
    max_overflow=30,       # Additional connections allowed
    pool_pre_ping=True,    # Validate connections before use
    pool_recycle=3600      # Recycle connections after 1 hour
)
```

### **2. Caching with Async Redis**

```python
import aioredis
from fastapi import Depends

redis_pool = None

async def get_redis():
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url("redis://localhost", decode_responses=True)
    return redis_pool

@app.get("/leaderboard/global")
async def get_global_leaderboard(redis = Depends(get_redis)):
    """Get cached global leaderboard"""
    
    # Try to get from cache first
    cached_leaderboard = await redis.get("global_leaderboard")
    if cached_leaderboard:
        return json.loads(cached_leaderboard)
    
    # If not cached, fetch from database
    leaderboard_data = await fetch_leaderboard_from_db()
    
    # Cache for 5 minutes
    await redis.setex("global_leaderboard", 300, json.dumps(leaderboard_data))
    
    return leaderboard_data
```

## 🎮 Key Gaming Endpoints

### **Game Management**
```python
@app.post("/games/create", response_model=GameResponse)
async def create_game(game_data: GameCreate, background_tasks: BackgroundTasks)

@app.get("/games/{game_id}/state")
async def get_game_state(game_id: str)

@app.post("/games/{game_id}/join")
async def join_game(game_id: str, player_id: int)
```

### **Real-time Features**
```python
@app.websocket("/games/{game_id}/live")
async def game_websocket(websocket: WebSocket, game_id: str)

@app.websocket("/tournaments/{tournament_id}/updates")
async def tournament_updates(websocket: WebSocket, tournament_id: int)
```

## 🛠️ Running the Gaming Platform

```bash
cd 07-async
uvicorn main:app --reload --workers 4

# Test WebSocket connections:
# ws://localhost:8000/games/room1/live
# ws://localhost:8000/chat/general
```

## 📊 Async vs Sync Performance

| Operation | Sync API | Async API | Improvement |
|-----------|----------|-----------|-------------|
| **Single Request** | 200ms | 200ms | No difference |
| **100 Concurrent** | 20 seconds | 2 seconds | 10x faster |
| **1000 Concurrent** | 200 seconds | 5 seconds | 40x faster |
| **Memory Usage** | High | Low | 70% reduction |

## 🎮 Practice Exercises

1. **🏆 Tournament System**: Create async tournament bracket management
2. **📊 Real-time Analytics**: Build live player statistics dashboard
3. **🎯 Matchmaking**: Implement async player matching algorithms
4. **💾 Data Streaming**: Process large game logs asynchronously

## 💡 Async Best Practices

### **Do's:**
- Use `async def` for I/O operations (database, API calls)
- Leverage `asyncio.gather()` for concurrent operations
- Implement connection pooling for databases
- Use background tasks for non-critical operations

### **Don'ts:**
- Don't use blocking operations in async functions
- Avoid creating too many concurrent tasks
- Don't forget error handling in background tasks
- Don't mix sync and async code carelessly

## ⚡ Performance Tips

### **Concurrency Patterns**
- **CPU-bound tasks**: Use `asyncio.to_thread()` or process pools
- **I/O-bound tasks**: Use `async/await` with proper connection pooling
- **Real-time updates**: Use WebSockets with efficient broadcasting
- **Background processing**: Use FastAPI BackgroundTasks or Celery

## 🚀 What's Next?

In **Section 8: Streaming**, we'll build a live content streaming platform that shows how to handle real-time data streams, file uploads, and server-sent events!

**Key Takeaway**: Async programming is essential for modern web applications - it allows your API to handle thousands of users simultaneously without breaking a sweat! 🎮⚡ 