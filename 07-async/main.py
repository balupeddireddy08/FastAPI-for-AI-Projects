import asyncio
import httpx
import time
import json
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from datetime import datetime

app = FastAPI(
    title="FastAPI Async Demo",
    description="Demonstration of asynchronous programming in FastAPI",
    version="0.1.0"
)

# Basic async endpoint
@app.get("/")
async def read_root():
    """Simple async endpoint returning a welcome message."""
    return {"message": "Welcome to FastAPI Async Demo"}

# Simulated database client
class AsyncDBClient:
    def __init__(self):
        # Simulating a database connection
        self.db = {}
        # Pre-populate with some data
        self.db["users"] = [
            {"id": 1, "name": "John", "email": "john@example.com"},
            {"id": 2, "name": "Jane", "email": "jane@example.com"}
        ]
        
    async def connect(self):
        # Simulate connection delay
        await asyncio.sleep(0.1)
        print("Database connected")
        
    async def close(self):
        # Simulate closing delay
        await asyncio.sleep(0.1)
        print("Database disconnected")
        
    async def fetch_one(self, collection, id):
        # Simulate database fetch delay
        await asyncio.sleep(0.2)
        items = self.db.get(collection, [])
        for item in items:
            if item.get("id") == id:
                return item
        return None
        
    async def fetch_all(self, collection):
        # Simulate database fetch delay
        await asyncio.sleep(0.2)
        return self.db.get(collection, [])
        
    async def insert(self, collection, data):
        # Simulate database insertion delay
        await asyncio.sleep(0.2)
        if collection not in self.db:
            self.db[collection] = []
        self.db[collection].append(data)
        return data

# Create a database instance
db_client = AsyncDBClient()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    await db_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db_client.close()

# Database dependency
async def get_db():
    try:
        yield db_client
    finally:
        # No need to close it per request in this example
        pass

# Async database query
@app.get("/users/{user_id}")
async def get_user(user_id: int, db=Depends(get_db)):
    """Get a user from the database asynchronously."""
    user = await db.fetch_one("users", user_id)
    if user:
        return user
    return {"error": "User not found"}

# Async with external API calls
@app.get("/api/{item_id}")
async def proxy_request(item_id: str):
    """
    Make an async request to an external API.
    
    This demonstrates how to make external HTTP requests asynchronously.
    """
    # Using a fake API for demonstration
    async with httpx.AsyncClient() as client:
        # Simulate API call
        await asyncio.sleep(1)  # Simulated API delay
        return {
            "item_id": item_id,
            "name": f"Item {item_id}",
            "timestamp": datetime.now().isoformat()
        }

# Multiple concurrent API calls
async def fetch_resource(resource_name: str):
    """Simulate fetching a resource from an external API."""
    # Simulate different API response times
    delay = {
        "users": 1.0,
        "products": 0.8,
        "weather": 1.2,
        "news": 0.5
    }.get(resource_name, 1.0)
    
    await asyncio.sleep(delay)
    
    # Return simulated data
    return {
        "resource": resource_name,
        "data": f"Data for {resource_name}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dashboard")
async def get_dashboard():
    """
    Fetch multiple resources concurrently.
    
    This demonstrates how to run multiple async operations concurrently
    and combine their results.
    """
    start_time = time.time()
    
    # Execute API calls concurrently
    tasks = [
        fetch_resource("users"),
        fetch_resource("products"),
        fetch_resource("weather"),
        fetch_resource("news")
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Organize results into a dictionary
    dashboard_data = {result["resource"]: result for result in results}
    dashboard_data["execution_time"] = execution_time
    
    return dashboard_data

# Background task example
def process_data_in_background(data: Dict[str, Any]):
    """Simulate a time-consuming background process."""
    # In a real application, this might be sending emails,
    # processing files, or updating a database
    time.sleep(5)  # Simulating a time-consuming task
    print(f"Background processing complete for data: {data}")

@app.post("/data/")
async def create_data(data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Create data and process it in the background.
    
    This demonstrates how to use background tasks to perform work
    after returning a response to the client.
    """
    # Schedule the background task
    background_tasks.add_task(process_data_in_background, data)
    
    return {
        "message": "Data received, processing started",
        "data_id": hash(str(data)),
        "timestamp": datetime.now().isoformat()
    }

# CPU-bound task handled correctly
def fibonacci(n: int) -> int:
    """Calculate fibonacci number (CPU-intensive task)."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Create a process pool
process_executor = ProcessPoolExecutor()

@app.get("/fibonacci/{n}")
async def get_fibonacci(n: int):
    """
    Calculate fibonacci number using a process pool.
    
    This demonstrates how to handle CPU-bound tasks without
    blocking the event loop.
    """
    if n > 30:
        return {"error": "Input too large, maximum allowed is 30"}
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        process_executor,
        partial(fibonacci, n)
    )
    
    return {"n": n, "result": result}

# WebSocket implementation
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI WebSocket Chat</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            #messages {
                list-style-type: none;
                padding: 0;
                margin: 20px 0;
            }
            #messages li {
                padding: 5px 10px;
                background-color: #f1f1f1;
                margin-bottom: 5px;
                border-radius: 3px;
            }
            form {
                display: flex;
            }
            input {
                flex-grow: 1;
                padding: 8px;
                margin-right: 10px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            button {
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" placeholder="Type a message..."/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""

@app.get("/chat", response_class=HTMLResponse)
async def get_chat():
    """Serve HTML page with WebSocket chat client."""
    return html

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.
    
    This demonstrates how to use WebSockets for bidirectional
    communication with clients.
    """
    await websocket.accept()
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            # Send message back to client with timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            await websocket.send_text(f"[{timestamp}] Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")

# Practice Exercise Solution

# Model for API response data
class APIResponse(BaseModel):
    source: str
    data: Dict[str, Any]
    timestamp: str

# External API clients (simulated)
class WeatherAPI:
    """Simulated weather API client."""
    
    @staticmethod
    async def get_weather(city: str) -> Dict[str, Any]:
        # Simulate API delay
        await asyncio.sleep(1.2)
        return {
            "city": city,
            "temperature": 22.5,
            "condition": "Sunny",
            "humidity": 60,
            "wind_speed": 5.7
        }

class NewsAPI:
    """Simulated news API client."""
    
    @staticmethod
    async def get_top_headlines(category: str = "technology") -> List[Dict[str, Any]]:
        # Simulate API delay
        await asyncio.sleep(0.9)
        return [
            {
                "title": "New AI breakthrough announced",
                "source": "Tech News Daily",
                "published_at": "2023-06-15T08:30:00Z"
            },
            {
                "title": "Python 3.11 shows impressive performance gains",
                "source": "Programming Weekly",
                "published_at": "2023-06-14T14:15:00Z"
            }
        ]

class StockAPI:
    """Simulated stock market API client."""
    
    @staticmethod
    async def get_stock_price(symbol: str) -> Dict[str, Any]:
        # Simulate API delay
        await asyncio.sleep(0.7)
        return {
            "symbol": symbol,
            "price": 142.5,
            "change": 0.75,
            "change_percent": 0.53
        }

# Practice Exercise 1: Endpoint fetching data from multiple APIs concurrently
@app.get("/dashboard/{city}/{stock}")
async def multi_api_dashboard(
    city: str,
    stock: str,
    news_category: Optional[str] = "technology"
):
    """
    Fetch data from multiple external APIs concurrently.
    
    This endpoint demonstrates how to make multiple API calls concurrently
    and combine their results into a single response.
    """
    start_time = time.time()
    
    # Make API calls concurrently
    weather_task = WeatherAPI.get_weather(city)
    news_task = NewsAPI.get_top_headlines(news_category)
    stock_task = StockAPI.get_stock_price(stock)
    
    # Wait for all tasks to complete
    weather_data, news_data, stock_data = await asyncio.gather(
        weather_task, news_task, stock_task
    )
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Combine results
    return {
        "weather": weather_data,
        "news": news_data,
        "stock": stock_data,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat()
    }

# Practice Exercise 2: Background task processing
def analyze_data_in_background(data: Dict[str, Any]):
    """Simulate complex data analysis in the background."""
    print(f"Starting analysis of data at {datetime.now().isoformat()}")
    
    # Simulate complex processing
    time.sleep(10)
    
    # Calculate some "results"
    result = {
        "processed_at": datetime.now().isoformat(),
        "input_size": len(str(data)),
        "sentiment_score": 0.75,
        "complexity_score": 0.62,
        "tags": ["ai", "data", "analysis"]
    }
    
    # In a real application, you might save this to a database
    # or send a notification when complete
    print(f"Analysis complete: {result}")

@app.post("/analyze/")
async def analyze_data(data: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Submit data for background analysis.
    
    This endpoint accepts data, schedules it for background processing,
    and returns immediately with a tracking ID.
    """
    # Generate a tracking ID
    tracking_id = f"analysis_{int(time.time())}_{hash(str(data)) % 10000}"
    
    # Schedule the background task
    background_tasks.add_task(analyze_data_in_background, data)
    
    return {
        "message": "Analysis started",
        "tracking_id": tracking_id,
        "submitted_at": datetime.now().isoformat(),
        "estimated_completion_time": "10 seconds"
    }

# Practice Exercise 3: WebSocket for real-time updates
class ConnectionManager:
    """Manage WebSocket connections and broadcasts."""
    
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

@app.websocket("/updates")
async def websocket_updates(websocket: WebSocket):
    """
    WebSocket endpoint providing real-time updates.
    
    Clients connecting to this WebSocket will receive periodic updates
    simulating a real-time data feed.
    """
    await manager.connect(websocket)
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "info",
            "message": "Connected to update stream",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Send periodic updates
        counter = 0
        while True:
            # Wait a bit between updates
            await asyncio.sleep(2)
            counter += 1
            
            # Create update data
            update = {
                "type": "update",
                "update_id": counter,
                "data": {
                    "value": counter * 1.5,
                    "trend": "up" if counter % 3 != 0 else "down",
                    "alerts": counter % 5 == 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to this client
            await websocket.send_text(json.dumps(update))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# HTML page for real-time updates demo
updates_html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI Real-time Updates</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            #updates {
                list-style-type: none;
                padding: 0;
                margin: 20px 0;
            }
            #updates li {
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 5px;
            }
            .info {
                background-color: #e1f5fe;
                border-left: 5px solid #03a9f4;
            }
            .update {
                background-color: #f1f8e9;
                border-left: 5px solid #8bc34a;
            }
            .update.alert {
                background-color: #ffebee;
                border-left: 5px solid #f44336;
            }
            .timestamp {
                font-size: 0.8em;
                color: #666;
                display: block;
                margin-top: 5px;
            }
            .trend-up {
                color: green;
            }
            .trend-down {
                color: red;
            }
        </style>
    </head>
    <body>
        <h1>Real-time Data Updates</h1>
        <div>
            <p>This page demonstrates real-time updates using WebSockets.</p>
            <p>Connection status: <span id="status">Connecting...</span></p>
        </div>
        <ul id="updates"></ul>
        <script>
            // Connect to WebSocket
            const ws = new WebSocket("ws://localhost:8000/updates");
            const updatesList = document.getElementById('updates');
            const statusDisplay = document.getElementById('status');
            
            ws.onopen = function() {
                statusDisplay.textContent = "Connected";
                statusDisplay.style.color = "green";
            };
            
            ws.onclose = function() {
                statusDisplay.textContent = "Disconnected";
                statusDisplay.style.color = "red";
            };
            
            ws.onerror = function() {
                statusDisplay.textContent = "Error";
                statusDisplay.style.color = "red";
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const item = document.createElement('li');
                
                // Style based on message type
                if (data.type === "info") {
                    item.className = "info";
                    item.innerHTML = `<strong>Info:</strong> ${data.message}`;
                } else if (data.type === "update") {
                    item.className = data.data.alerts ? "update alert" : "update";
                    
                    // Format trend with arrow
                    const trendClass = data.data.trend === "up" ? "trend-up" : "trend-down";
                    const trendArrow = data.data.trend === "up" ? "↑" : "↓";
                    
                    item.innerHTML = `
                        <strong>Update #${data.update_id}</strong><br>
                        Value: ${data.data.value} 
                        <span class="${trendClass}">${trendArrow} ${data.data.trend}</span>
                        ${data.data.alerts ? '<br><strong>⚠️ Alert condition detected!</strong>' : ''}
                    `;
                }
                
                // Add timestamp
                const timestamp = document.createElement('span');
                timestamp.className = "timestamp";
                timestamp.textContent = new Date(data.timestamp).toLocaleString();
                item.appendChild(timestamp);
                
                // Add to list and scroll into view
                updatesList.appendChild(item);
                item.scrollIntoView({ behavior: "smooth" });
                
                // Keep only the last 20 updates
                while (updatesList.children.length > 20) {
                    updatesList.removeChild(updatesList.children[0]);
                }
            };
        </script>
    </body>
</html>
"""

@app.get("/real-time-updates", response_class=HTMLResponse)
async def get_updates_page():
    """Serve HTML page with WebSocket for real-time updates demo."""
    return updates_html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 