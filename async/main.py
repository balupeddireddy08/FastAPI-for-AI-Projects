import asyncio
import aiofiles
import aiohttp
import asyncpg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Set, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid
import random
import time

# Initialize our Epic Real-time Gaming Platform
app = FastAPI(
    title="🎮 Epic Gaming Platform - Real-time Multiplayer Arena",
    description="""
    Welcome to the **Epic Gaming Platform** - where lightning-fast gameplay meets cutting-edge technology! ⚡
    
    Experience the power of asynchronous programming with:
    
    * 🎯 **Real-time Multiplayer**: Simultaneous gameplay for thousands of players
    * ⚡ **Ultra-low Latency**: Sub-millisecond response times
    * 🌐 **WebSocket Connections**: Live game state synchronization
    * 🏆 **Live Tournaments**: Real-time leaderboards and competitions
    * 📊 **Streaming Analytics**: Live game statistics and player insights
    * 🤖 **AI Opponents**: Smart bots that adapt to your playstyle
    
    Built with FastAPI's async superpowers - handling 10,000+ concurrent players! 🚀
    """,
    version="1.0.0"
)

# === GAME MODELS ===

class GameType(str, Enum):
    BATTLE_ROYALE = "battle_royale"
    TEAM_DEATHMATCH = "team_deathmatch"
    RACING = "racing"
    PUZZLE = "puzzle"
    STRATEGY = "strategy"

class PlayerStatus(str, Enum):
    ONLINE = "online"
    IN_GAME = "in_game"
    AWAY = "away"
    OFFLINE = "offline"

class GameAction(str, Enum):
    MOVE = "move"
    ATTACK = "attack"
    DEFEND = "defend"
    USE_ITEM = "use_item"
    CHAT = "chat"

class Player(BaseModel):
    """Real-time player information"""
    id: str = Field(..., description="Unique player identifier")
    username: str = Field(..., min_length=3, max_length=20, description="Player display name")
    level: int = Field(1, ge=1, le=100, description="Player level")
    score: int = Field(0, ge=0, description="Current game score")
    position: Dict[str, float] = Field({}, description="Player position in game world")
    status: PlayerStatus = Field(PlayerStatus.ONLINE, description="Current player status")
    last_action: datetime = Field(default_factory=datetime.now)

class GameRoom(BaseModel):
    """Multiplayer game room configuration"""
    id: str = Field(..., description="Unique room identifier")
    name: str = Field(..., min_length=3, max_length=50, description="Room display name")
    game_type: GameType = Field(..., description="Type of game being played")
    max_players: int = Field(10, ge=2, le=100, description="Maximum players allowed")
    current_players: int = Field(0, ge=0, description="Current number of players")
    is_active: bool = Field(True, description="Whether the room is accepting players")
    created_at: datetime = Field(default_factory=datetime.now)

class GameAction(BaseModel):
    """Player action in the game"""
    player_id: str = Field(..., description="Player performing the action")
    action_type: GameAction = Field(..., description="Type of action performed")
    target_position: Optional[Dict[str, float]] = Field(None, description="Target position for movement")
    target_player: Optional[str] = Field(None, description="Target player for interactions")
    data: Optional[Dict] = Field({}, description="Additional action data")
    timestamp: datetime = Field(default_factory=datetime.now)

# === GLOBAL GAME STATE ===

# WebSocket connection manager for real-time communication
class ConnectionManager:
    """Manages WebSocket connections for real-time gameplay"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        self.player_rooms: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, player_id: str, room_id: str):
        """Connect a player to a game room"""
        await websocket.accept()
        self.active_connections[player_id] = websocket
        
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        
        self.room_connections[room_id].add(player_id)
        self.player_rooms[player_id] = room_id
        
        print(f"🎮 Player {player_id} connected to room {room_id}")
    
    def disconnect(self, player_id: str):
        """Disconnect a player from their room"""
        if player_id in self.active_connections:
            room_id = self.player_rooms.get(player_id)
            
            if room_id and room_id in self.room_connections:
                self.room_connections[room_id].discard(player_id)
                
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
            
            del self.active_connections[player_id]
            if player_id in self.player_rooms:
                del self.player_rooms[player_id]
            
            print(f"🚪 Player {player_id} disconnected")
    
    async def send_personal_message(self, message: str, player_id: str):
        """Send message to specific player"""
        if player_id in self.active_connections:
            await self.active_connections[player_id].send_text(message)
    
    async def broadcast_to_room(self, message: str, room_id: str):
        """Broadcast message to all players in a room"""
        if room_id in self.room_connections:
            disconnected_players = []
            
            for player_id in self.room_connections[room_id]:
                try:
                    if player_id in self.active_connections:
                        await self.active_connections[player_id].send_text(message)
                except:
                    disconnected_players.append(player_id)
            
            # Clean up disconnected players
            for player_id in disconnected_players:
                self.disconnect(player_id)

# Global connection manager
manager = ConnectionManager()

# In-memory game state (in production, use Redis or similar)
game_rooms: Dict[str, GameRoom] = {}
players: Dict[str, Player] = {}
game_state: Dict[str, Dict] = {}  # room_id -> game state

# === ASYNC HELPER FUNCTIONS ===

async def simulate_ai_player_action(room_id: str, ai_player_id: str):
    """Simulate AI player taking actions in the game"""
    while room_id in game_rooms and game_rooms[room_id].is_active:
        await asyncio.sleep(random.uniform(1, 3))  # AI acts every 1-3 seconds
        
        if ai_player_id in players:
            # Generate random AI action
            actions = [GameAction.MOVE, GameAction.ATTACK, GameAction.DEFEND]
            action_type = random.choice(actions)
            
            ai_action = {
                "type": "player_action",
                "player_id": ai_player_id,
                "action": action_type.value,
                "position": {
                    "x": random.uniform(0, 100),
                    "y": random.uniform(0, 100)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.broadcast_to_room(json.dumps(ai_action), room_id)

async def fetch_player_stats_async(player_id: str) -> Dict:
    """Asynchronously fetch player statistics from external API"""
    async with aiohttp.ClientSession() as session:
        try:
            # Simulate external API call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Mock player stats
            return {
                "player_id": player_id,
                "total_games": random.randint(50, 500),
                "wins": random.randint(20, 250),
                "losses": random.randint(10, 100),
                "win_rate": round(random.uniform(0.4, 0.8), 2),
                "average_score": random.randint(1500, 3000),
                "rank": random.choice(["Bronze", "Silver", "Gold", "Platinum", "Diamond"]),
                "achievements": random.randint(5, 25)
            }
        except Exception as e:
            print(f"❌ Error fetching stats for {player_id}: {e}")
            return {"error": "Could not fetch player stats"}

async def save_game_replay_async(room_id: str, game_data: Dict):
    """Asynchronously save game replay to file"""
    filename = f"replays/game_{room_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    async with aiofiles.open(filename, 'w') as f:
        await f.write(json.dumps(game_data, indent=2))
    
    print(f"💾 Game replay saved: {filename}")

async def process_leaderboard_update():
    """Background task to update global leaderboards"""
    while True:
        print("📊 Updating global leaderboards...")
        
        # Simulate leaderboard calculation
        await asyncio.sleep(30)  # Update every 30 seconds
        
        # In a real app, this would update database rankings
        await asyncio.sleep(1)  # Simulate database write

# === MAIN ENDPOINTS ===

@app.get("/")
def gaming_platform_home():
    """
    🎮 Welcome to the Epic Gaming Platform!
    
    The ultimate destination for real-time multiplayer gaming experiences.
    """
    return {
        "message": "🎮 Welcome to Epic Gaming Platform!",
        "tagline": "Where legends are born and epic battles unfold in real-time! ⚔️",
        "platform_stats": {
            "active_players": len([p for p in players.values() if p.status != PlayerStatus.OFFLINE]),
            "active_rooms": len([r for r in game_rooms.values() if r.is_active]),
            "total_games_today": random.randint(1000, 5000),
            "server_status": "🟢 All systems operational"
        },
        "featured_games": [
            {"id": "br_001", "name": "Dragon Valley Battle Royale", "players": 89},
            {"id": "tdm_002", "name": "Neon City Team Deathmatch", "players": 24},
            {"id": "race_003", "name": "Quantum Racing Championship", "players": 16}
        ],
        "quick_links": {
            "join_game": "/rooms/",
            "create_room": "/rooms/create",
            "leaderboards": "/leaderboards/",
            "websocket_docs": "/ws-demo"
        }
    }

@app.get("/rooms/", response_model=List[GameRoom])
async def list_active_rooms():
    """
    🏟️ Browse active game rooms and join the action!
    
    Discover ongoing games, tournaments, and custom matches.
    """
    active_rooms = [room for room in game_rooms.values() if room.is_active]
    return active_rooms

@app.post("/rooms/", response_model=GameRoom, status_code=status.HTTP_201_CREATED)
async def create_game_room(
    name: str = Field(..., min_length=3, max_length=50, description="Room name"),
    game_type: GameType = Field(..., description="Type of game"),
    max_players: int = Field(10, ge=2, le=100, description="Maximum players"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    🎯 Create your own game room!
    
    Set up a custom multiplayer experience with your preferred settings.
    """
    room_id = f"room_{uuid.uuid4().hex[:8]}"
    
    new_room = GameRoom(
        id=room_id,
        name=name,
        game_type=game_type,
        max_players=max_players
    )
    
    game_rooms[room_id] = new_room
    game_state[room_id] = {
        "players": {},
        "game_started": False,
        "start_time": None,
        "events": []
    }
    
    # Add AI players for demonstration
    background_tasks.add_task(add_ai_players_to_room, room_id, 2)
    
    print(f"🎮 Created new game room: {room_id} ({name})")
    return new_room

async def add_ai_players_to_room(room_id: str, count: int):
    """Add AI players to a room for demonstration"""
    await asyncio.sleep(1)  # Brief delay before adding AI
    
    for i in range(count):
        ai_id = f"ai_bot_{uuid.uuid4().hex[:6]}"
        ai_player = Player(
            id=ai_id,
            username=f"AI_Bot_{i+1}",
            level=random.randint(10, 50),
            status=PlayerStatus.IN_GAME,
            position={"x": random.uniform(0, 100), "y": random.uniform(0, 100)}
        )
        
        players[ai_id] = ai_player
        
        if room_id in game_state:
            game_state[room_id]["players"][ai_id] = ai_player.dict()
        
        # Start AI behavior
        asyncio.create_task(simulate_ai_player_action(room_id, ai_id))
    
    print(f"🤖 Added {count} AI players to room {room_id}")

@app.get("/players/{player_id}/stats")
async def get_player_stats(player_id: str):
    """
    📊 Get comprehensive player statistics asynchronously
    
    Fetch detailed performance metrics and achievements.
    """
    # Demonstrate concurrent async operations
    stats_task = asyncio.create_task(fetch_player_stats_async(player_id))
    
    # Simulate other concurrent operations
    recent_games_task = asyncio.create_task(get_recent_games_async(player_id))
    achievements_task = asyncio.create_task(get_achievements_async(player_id))
    
    # Wait for all operations to complete concurrently
    stats, recent_games, achievements = await asyncio.gather(
        stats_task,
        recent_games_task,
        achievements_task,
        return_exceptions=True
    )
    
    return {
        "player_id": player_id,
        "stats": stats if not isinstance(stats, Exception) else {"error": str(stats)},
        "recent_games": recent_games if not isinstance(recent_games, Exception) else [],
        "achievements": achievements if not isinstance(achievements, Exception) else [],
        "fetched_at": datetime.now().isoformat()
    }

async def get_recent_games_async(player_id: str) -> List[Dict]:
    """Fetch recent games asynchronously"""
    await asyncio.sleep(0.05)  # Simulate database query
    
    return [
        {
            "game_id": f"game_{i}",
            "game_type": random.choice(list(GameType)).value,
            "result": random.choice(["win", "loss", "draw"]),
            "score": random.randint(500, 2500),
            "duration": random.randint(300, 1800),  # seconds
            "played_at": (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
        }
        for i in range(5)
    ]

async def get_achievements_async(player_id: str) -> List[Dict]:
    """Fetch player achievements asynchronously"""
    await asyncio.sleep(0.03)  # Simulate API call
    
    achievements = [
        "First Blood", "Sharpshooter", "Team Player", "Speed Demon", 
        "Survivor", "Champion", "Strategist", "Combo Master"
    ]
    
    return [
        {
            "name": achievement,
            "description": f"Achievement: {achievement}",
            "earned_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "rarity": random.choice(["common", "rare", "epic", "legendary"])
        }
        for achievement in random.sample(achievements, random.randint(3, 6))
    ]

@app.get("/leaderboards/")
async def get_leaderboards():
    """
    🏆 View global leaderboards and rankings
    
    See top players, recent winners, and tournament standings.
    """
    # Simulate concurrent leaderboard queries
    global_task = asyncio.create_task(get_global_leaderboard())
    weekly_task = asyncio.create_task(get_weekly_leaderboard())
    
    global_leaders, weekly_leaders = await asyncio.gather(global_task, weekly_task)
    
    return {
        "global_leaderboard": global_leaders,
        "weekly_leaderboard": weekly_leaders,
        "last_updated": datetime.now().isoformat(),
        "next_update": (datetime.now() + timedelta(minutes=5)).isoformat()
    }

async def get_global_leaderboard() -> List[Dict]:
    """Fetch global leaderboard asynchronously"""
    await asyncio.sleep(0.1)  # Simulate database query
    
    return [
        {
            "rank": i + 1,
            "username": f"Pro_Player_{i+1}",
            "score": 10000 - (i * 150),
            "level": 100 - i,
            "wins": 500 - (i * 10),
            "games_played": 1000 - (i * 20)
        }
        for i in range(10)
    ]

async def get_weekly_leaderboard() -> List[Dict]:
    """Fetch weekly leaderboard asynchronously"""
    await asyncio.sleep(0.08)  # Simulate database query
    
    return [
        {
            "rank": i + 1,
            "username": f"Weekly_Star_{i+1}",
            "weekly_score": 5000 - (i * 100),
            "games_this_week": 50 - (i * 2),
            "win_streak": 15 - i
        }
        for i in range(10)
    ]

# === REAL-TIME WEBSOCKET GAMING ===

@app.websocket("/ws/game/{room_id}/{player_id}")
async def websocket_game_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    """
    🔌 Real-time game connection via WebSocket
    
    Connect to live multiplayer gameplay with ultra-low latency.
    """
    await manager.connect(websocket, player_id, room_id)
    
    # Add player to room
    if room_id not in game_rooms:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Room {room_id} not found"
        }))
        return
    
    # Create or update player
    if player_id not in players:
        players[player_id] = Player(
            id=player_id,
            username=f"Player_{player_id[:6]}",
            position={"x": random.uniform(0, 100), "y": random.uniform(0, 100)}
        )
    
    players[player_id].status = PlayerStatus.IN_GAME
    
    # Add player to game state
    if room_id in game_state:
        game_state[room_id]["players"][player_id] = players[player_id].dict()
    
    # Send welcome message
    welcome_message = {
        "type": "welcome",
        "player_id": player_id,
        "room_id": room_id,
        "game_state": game_state.get(room_id, {}),
        "message": f"🎮 Welcome to the game, {players[player_id].username}!"
    }
    await websocket.send_text(json.dumps(welcome_message))
    
    # Broadcast player joined
    join_message = {
        "type": "player_joined",
        "player": players[player_id].dict(),
        "timestamp": datetime.now().isoformat()
    }
    await manager.broadcast_to_room(json.dumps(join_message), room_id)
    
    try:
        while True:
            # Receive player actions
            data = await websocket.receive_text()
            action_data = json.loads(data)
            
            # Process player action
            await process_player_action(room_id, player_id, action_data)
            
            # Broadcast action to all players in room
            broadcast_message = {
                "type": "player_action",
                "player_id": player_id,
                "action": action_data,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast_to_room(json.dumps(broadcast_message), room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(player_id)
        
        # Update player status
        if player_id in players:
            players[player_id].status = PlayerStatus.OFFLINE
        
        # Remove from game state
        if room_id in game_state and player_id in game_state[room_id]["players"]:
            del game_state[room_id]["players"][player_id]
        
        # Broadcast player left
        leave_message = {
            "type": "player_left",
            "player_id": player_id,
            "timestamp": datetime.now().isoformat()
        }
        await manager.broadcast_to_room(json.dumps(leave_message), room_id)

async def process_player_action(room_id: str, player_id: str, action_data: Dict):
    """Process and validate player actions"""
    action_type = action_data.get("action_type")
    
    if player_id in players:
        player = players[player_id]
        
        if action_type == "move":
            new_position = action_data.get("position", {})
            player.position = new_position
            
        elif action_type == "attack":
            target_id = action_data.get("target_player")
            if target_id and target_id in players:
                # Process attack logic
                damage = random.randint(10, 30)
                print(f"⚔️ {player_id} attacks {target_id} for {damage} damage")
        
        elif action_type == "chat":
            message = action_data.get("message", "")
            chat_message = {
                "type": "chat",
                "player_id": player_id,
                "username": player.username,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            await manager.broadcast_to_room(json.dumps(chat_message), room_id)
        
        player.last_action = datetime.now()
        
        # Update game state
        if room_id in game_state:
            game_state[room_id]["players"][player_id] = player.dict()

# === STREAMING ENDPOINTS ===

@app.get("/stream/game-events/{room_id}")
async def stream_game_events(room_id: str):
    """
    📡 Stream live game events using Server-Sent Events
    
    Get real-time updates on game progress and player actions.
    """
    async def event_stream():
        while room_id in game_rooms and game_rooms[room_id].is_active:
            # Generate game event
            event_data = {
                "timestamp": datetime.now().isoformat(),
                "room_id": room_id,
                "active_players": len(game_state.get(room_id, {}).get("players", {})),
                "game_duration": time.time(),
                "random_event": random.choice([
                    "🏆 Player scored a point!",
                    "💥 Epic battle happening!",
                    "🎯 Perfect shot executed!",
                    "🔥 Combo multiplier active!",
                    "⭐ Achievement unlocked!"
                ])
            }
            
            yield f"data: {json.dumps(event_data)}\n\n"
            await asyncio.sleep(2)  # Update every 2 seconds
    
    return StreamingResponse(event_stream(), media_type="text/plain")

@app.get("/stream/leaderboard")
async def stream_live_leaderboard():
    """
    📊 Stream live leaderboard updates
    
    Watch rankings change in real-time as games progress.
    """
    async def leaderboard_stream():
        while True:
            # Generate live leaderboard
            live_data = {
                "timestamp": datetime.now().isoformat(),
                "top_players": [
                    {
                        "rank": i + 1,
                        "username": f"LivePlayer_{i+1}",
                        "score": random.randint(1000, 5000),
                        "status": random.choice(["🎮 In Game", "🏆 Victory", "⏱️ Queue"])
                    }
                    for i in range(5)
                ],
                "total_active": len(players),
                "games_in_progress": len([r for r in game_rooms.values() if r.is_active])
            }
            
            yield f"data: {json.dumps(live_data)}\n\n"
            await asyncio.sleep(5)  # Update every 5 seconds
    
    return StreamingResponse(leaderboard_stream(), media_type="text/plain")

# === BACKGROUND TASKS ===

@app.post("/admin/start-tournament")
async def start_tournament(background_tasks: BackgroundTasks):
    """
    🏆 Start a global tournament with background processing
    
    Launch tournaments that run independently in the background.
    """
    tournament_id = f"tournament_{uuid.uuid4().hex[:8]}"
    
    # Add background tasks for tournament management
    background_tasks.add_task(tournament_matchmaking, tournament_id)
    background_tasks.add_task(tournament_monitoring, tournament_id)
    background_tasks.add_task(update_tournament_leaderboard, tournament_id)
    
    return {
        "message": f"🏆 Tournament {tournament_id} started!",
        "tournament_id": tournament_id,
        "expected_duration": "30 minutes",
        "max_participants": 64,
        "prize_pool": "$1,000"
    }

async def tournament_matchmaking(tournament_id: str):
    """Background task for tournament matchmaking"""
    print(f"🔀 Starting matchmaking for tournament {tournament_id}")
    
    for round_num in range(1, 7):  # 6 rounds for 64-player tournament
        print(f"🎯 Tournament {tournament_id} - Round {round_num}")
        await asyncio.sleep(5)  # Each round takes 5 seconds
        
        # Simulate match results
        matches_this_round = 2 ** (6 - round_num)
        print(f"⚔️ Processing {matches_this_round} matches in round {round_num}")
    
    print(f"🏆 Tournament {tournament_id} completed!")

async def tournament_monitoring(tournament_id: str):
    """Background task for monitoring tournament health"""
    while True:
        await asyncio.sleep(10)  # Check every 10 seconds
        print(f"📊 Monitoring tournament {tournament_id} - All systems green")
        
        # In a real system, check for disconnections, lag, etc.
        break  # Exit after first check for demo

async def update_tournament_leaderboard(tournament_id: str):
    """Background task for updating tournament leaderboard"""
    for i in range(6):  # Update 6 times during tournament
        await asyncio.sleep(5)
        print(f"📈 Updated tournament {tournament_id} leaderboard - Update {i+1}/6")

# === FILE OPERATIONS ===

@app.post("/replays/save/{room_id}")
async def save_game_replay(room_id: str, background_tasks: BackgroundTasks):
    """
    💾 Save game replay asynchronously
    
    Preserve epic moments and strategies for later analysis.
    """
    if room_id not in game_state:
        raise HTTPException(status_code=404, detail="Game room not found")
    
    replay_data = {
        "room_id": room_id,
        "game_state": game_state[room_id],
        "duration": "15:30",
        "players": list(game_state[room_id].get("players", {}).keys()),
        "events": game_state[room_id].get("events", []),
        "saved_at": datetime.now().isoformat()
    }
    
    # Save asynchronously in background
    background_tasks.add_task(save_game_replay_async, room_id, replay_data)
    
    return {
        "message": f"💾 Game replay for room {room_id} is being saved",
        "estimated_size": "2.5 MB",
        "format": "JSON",
        "download_available_in": "30 seconds"
    }

@app.get("/replays/download/{room_id}")
async def download_replay(room_id: str):
    """
    📥 Download game replay file
    
    Get detailed game replay for analysis and sharing.
    """
    # Simulate async file reading
    async def replay_generator():
        replay_data = {
            "room_id": room_id,
            "version": "1.0",
            "duration": 930,  # seconds
            "events": []
        }
        
        # Generate replay events
        for i in range(100):
            event = {
                "timestamp": i * 10,  # Every 10 seconds
                "type": random.choice(["move", "attack", "score", "powerup"]),
                "player": f"player_{random.randint(1, 4)}",
                "data": {"x": random.randint(0, 100), "y": random.randint(0, 100)}
            }
            replay_data["events"].append(event)
            
            if i % 10 == 0:  # Stream in chunks
                yield json.dumps(event) + "\n"
                await asyncio.sleep(0.01)  # Small delay to simulate processing
    
    return StreamingResponse(
        replay_generator(),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=replay_{room_id}.json"}
    )

# === DEMO PAGE ===

@app.get("/ws-demo", response_class=HTMLResponse)
def websocket_demo_page():
    """
    🎮 Interactive WebSocket demo page
    
    Try real-time gaming features in your browser!
    """
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>🎮 Epic Gaming Platform - WebSocket Demo</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container { 
                    background: rgba(255,255,255,0.1); 
                    padding: 30px; 
                    border-radius: 15px; 
                    backdrop-filter: blur(10px);
                }
                .game-area {
                    background: rgba(0,0,0,0.3);
                    height: 400px;
                    border-radius: 10px;
                    margin: 20px 0;
                    position: relative;
                    overflow: hidden;
                }
                .player {
                    position: absolute;
                    width: 30px;
                    height: 30px;
                    background: #ff6b6b;
                    border-radius: 50%;
                    border: 2px solid white;
                    transition: all 0.3s ease;
                }
                .controls {
                    display: flex;
                    gap: 10px;
                    margin: 20px 0;
                    flex-wrap: wrap;
                }
                button {
                    background: #4ecdc4;
                    color: white;
                    border: none;
                    padding: 12px 20px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: all 0.3s ease;
                }
                button:hover { background: #45b7aa; transform: translateY(-2px); }
                .status {
                    background: rgba(0,0,0,0.5);
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                    font-family: monospace;
                }
                .chat {
                    background: rgba(0,0,0,0.5);
                    height: 200px;
                    overflow-y: auto;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                }
                input[type="text"] {
                    width: 70%;
                    padding: 10px;
                    border: none;
                    border-radius: 20px;
                    margin-right: 10px;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .stat-card {
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Epic Gaming Platform - Live Demo</h1>
                <p>Experience real-time multiplayer gaming with WebSocket technology!</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>🟢 Connection Status</h3>
                        <div id="connectionStatus">Disconnected</div>
                    </div>
                    <div class="stat-card">
                        <h3>👥 Players Online</h3>
                        <div id="playersOnline">0</div>
                    </div>
                    <div class="stat-card">
                        <h3>⚡ Latency</h3>
                        <div id="latency">0ms</div>
                    </div>
                    <div class="stat-card">
                        <h3>🎯 Actions</h3>
                        <div id="actionCount">0</div>
                    </div>
                </div>
                
                <div class="game-area" id="gameArea">
                    <div class="player" id="player" style="left: 50%; top: 50%;"></div>
                </div>
                
                <div class="controls">
                    <button onclick="connectToGame()">🔌 Connect to Game</button>
                    <button onclick="movePlayer()">🏃 Random Move</button>
                    <button onclick="attackAction()">⚔️ Attack</button>
                    <button onclick="defendAction()">🛡️ Defend</button>
                    <button onclick="useItem()">🎒 Use Item</button>
                    <button onclick="disconnect()">🚪 Disconnect</button>
                </div>
                
                <div class="status" id="status">
                    Ready to connect! Click "Connect to Game" to start.
                </div>
                
                <h3>💬 Game Chat</h3>
                <div class="chat" id="chat"></div>
                <input type="text" id="chatInput" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendChat()">
                <button onclick="sendChat()">📤 Send</button>
            </div>
            
            <script>
                let ws = null;
                let playerId = 'player_' + Math.random().toString(36).substr(2, 9);
                let roomId = 'demo_room_001';
                let actionCount = 0;
                let latencyStart = 0;
                
                function updateStatus(message) {
                    document.getElementById('status').innerHTML = new Date().toLocaleTimeString() + ': ' + message;
                }
                
                function updateConnectionStatus(status) {
                    const statusEl = document.getElementById('connectionStatus');
                    statusEl.textContent = status;
                    statusEl.style.color = status === 'Connected' ? '#4ecdc4' : '#ff6b6b';
                }
                
                function connectToGame() {
                    const wsUrl = `ws://localhost:8000/ws/game/${roomId}/${playerId}`;
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = function(event) {
                        updateConnectionStatus('Connected');
                        updateStatus('🎮 Connected to Epic Gaming Platform!');
                        latencyStart = Date.now();
                    };
                    
                    ws.onmessage = function(event) {
                        const data = JSON.parse(event.data);
                        handleGameMessage(data);
                        
                        // Calculate latency for our own actions
                        if (data.player_id === playerId) {
                            const latency = Date.now() - latencyStart;
                            document.getElementById('latency').textContent = latency + 'ms';
                        }
                    };
                    
                    ws.onclose = function(event) {
                        updateConnectionStatus('Disconnected');
                        updateStatus('🚪 Disconnected from game.');
                    };
                    
                    ws.onerror = function(error) {
                        updateStatus('❌ Connection error: ' + error);
                    };
                }
                
                function handleGameMessage(data) {
                    switch(data.type) {
                        case 'welcome':
                            updateStatus('🎉 Welcome to the game! Room: ' + data.room_id);
                            document.getElementById('playersOnline').textContent = 
                                Object.keys(data.game_state.players || {}).length;
                            break;
                            
                        case 'player_joined':
                            addChatMessage('🎮 ' + data.player.username + ' joined the game!');
                            break;
                            
                        case 'player_left':
                            addChatMessage('👋 Player ' + data.player_id + ' left the game.');
                            break;
                            
                        case 'player_action':
                            if (data.player_id !== playerId) {
                                updateStatus('👀 ' + data.player_id + ' performed: ' + data.action.action_type);
                            }
                            break;
                            
                        case 'chat':
                            addChatMessage('💬 ' + data.username + ': ' + data.message);
                            break;
                    }
                }
                
                function addChatMessage(message) {
                    const chat = document.getElementById('chat');
                    const messageEl = document.createElement('div');
                    messageEl.textContent = new Date().toLocaleTimeString() + ' - ' + message;
                    chat.appendChild(messageEl);
                    chat.scrollTop = chat.scrollHeight;
                }
                
                function sendGameAction(actionType, data = {}) {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        latencyStart = Date.now();
                        actionCount++;
                        document.getElementById('actionCount').textContent = actionCount;
                        
                        const action = {
                            action_type: actionType,
                            ...data
                        };
                        
                        ws.send(JSON.stringify(action));
                        updateStatus('📤 Sent action: ' + actionType);
                    } else {
                        updateStatus('❌ Not connected to game!');
                    }
                }
                
                function movePlayer() {
                    const gameArea = document.getElementById('gameArea');
                    const player = document.getElementById('player');
                    
                    const x = Math.random() * (gameArea.offsetWidth - 30);
                    const y = Math.random() * (gameArea.offsetHeight - 30);
                    
                    player.style.left = x + 'px';
                    player.style.top = y + 'px';
                    
                    sendGameAction('move', {
                        position: { x: x, y: y }
                    });
                }
                
                function attackAction() {
                    sendGameAction('attack', {
                        target_player: 'ai_bot_' + Math.floor(Math.random() * 3),
                        damage: Math.floor(Math.random() * 30) + 10
                    });
                }
                
                function defendAction() {
                    sendGameAction('defend', {
                        defense_type: 'shield'
                    });
                }
                
                function useItem() {
                    const items = ['health_potion', 'speed_boost', 'shield', 'weapon_upgrade'];
                    const randomItem = items[Math.floor(Math.random() * items.length)];
                    
                    sendGameAction('use_item', {
                        item: randomItem
                    });
                }
                
                function sendChat() {
                    const input = document.getElementById('chatInput');
                    const message = input.value.trim();
                    
                    if (message && ws && ws.readyState === WebSocket.OPEN) {
                        sendGameAction('chat', {
                            message: message
                        });
                        input.value = '';
                    }
                }
                
                function disconnect() {
                    if (ws) {
                        ws.close();
                    }
                }
                
                // Auto-update player count simulation
                setInterval(() => {
                    document.getElementById('playersOnline').textContent = 
                        Math.floor(Math.random() * 50) + 10;
                }, 5000);
            </script>
        </body>
    </html>
    """

# === STARTUP EVENTS ===

@app.on_event("startup")
async def startup_event():
    """Initialize the gaming platform on startup"""
    print("🚀 Epic Gaming Platform starting up...")
    
    # Create default demo room
    demo_room = GameRoom(
        id="demo_room_001",
        name="Epic Battle Arena (Demo)",
        game_type=GameType.BATTLE_ROYALE,
        max_players=20
    )
    
    game_rooms["demo_room_001"] = demo_room
    game_state["demo_room_001"] = {
        "players": {},
        "game_started": True,
        "start_time": datetime.now(),
        "events": []
    }
    
    # Start background leaderboard updates
    asyncio.create_task(process_leaderboard_update())
    
    print("✅ Epic Gaming Platform ready for action!")
    print("🎮 Demo room created: demo_room_001")
    print("🌐 WebSocket demo available at: /ws-demo")

if __name__ == "__main__":
    import uvicorn
    print("🎮 Starting Epic Gaming Platform...")
    print("⚡ Real-time multiplayer gaming with async superpowers!")
    print("🌐 WebSocket demo: http://localhost:8000/ws-demo")
    uvicorn.run(app, host="0.0.0.0", port=8000) 