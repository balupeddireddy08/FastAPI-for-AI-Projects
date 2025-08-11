import asyncio
import json
import random
from datetime import datetime
from typing import List, Dict

from fastapi import (
    FastAPI,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse, StreamingResponse

# --- App Setup ---
# This creates the main FastAPI application instance.
# Think of this as the central kitchen for our food delivery service.
app = FastAPI(
    title="🚀 Food Delivery App - FastAPI Async Showcase",
    description="A cohesive example using a Food Delivery App to demonstrate async features.",
    version="2.0.0",
)

# --- In-Memory 'Database' & State ---
# Simple Python dictionaries to act as a temporary database for our demo.
# In a real app, this would be a proper database like PostgreSQL.
fake_db = {
    "restaurants": {
        "resto_123": {"name": "The Spicy Spoon", "cuisine": "Indian", "rating": 4.7},
        "resto_456": {"name": "Pasta Paradise", "cuisine": "Italian", "rating": 4.5},
        "resto_789": {"name": "Sushi Supreme", "cuisine": "Japanese", "rating": 4.8},
        "resto_101": {"name": "Burger Bliss", "cuisine": "American", "rating": 4.2},
        "resto_202": {"name": "Taco Temple", "cuisine": "Mexican", "rating": 4.6},
    },
    "orders": {},
    "menus": {
        "resto_123": ["Butter Chicken", "Naan", "Samosa", "Chicken Tikka Masala", "Biryani"],
        "resto_456": ["Spaghetti Carbonara", "Margherita Pizza", "Lasagna", "Tiramisu", "Risotto"],
        "resto_789": ["California Roll", "Sashimi Platter", "Tempura", "Miso Soup", "Dragon Roll"],
        "resto_101": ["Cheeseburger", "Bacon Burger", "Veggie Burger", "Loaded Fries", "Milkshake"],
        "resto_202": ["Street Tacos", "Burrito", "Quesadilla", "Nachos Supreme", "Guacamole"],
    }
}
# A manager for WebSocket chat rooms will be created below, with the WebSocket code.


# ===================================================================================
# FEATURE 1: Basic Async/Await Endpoint (The Skilled Waiter)
# ===================================================================================
# ANALOGY: A skilled waiter takes your order, gives it to the kitchen, and immediately
# serves other tables. They don't stand around waiting for your food. This `async`
# function is like that waiter—it efficiently handles requests without blocking.

@app.get("/restaurants/{restaurant_id}")
async def get_restaurant_info(restaurant_id: str):
    """
    A basic async endpoint to fetch restaurant details.
    Simulates a non-blocking database call.
    """
    print(f"Fetching details for restaurant {restaurant_id}...")
    # `await asyncio.sleep(3)` simulates a database query.
    # While "waiting", the server can handle other requests.
    await asyncio.sleep(3)
    return fake_db["restaurants"].get(restaurant_id, {"error": "Restaurant not found"})


# ===================================================================================
# FEATURE 2: Concurrent Tasks (Ordering Coffee & A Sandwich)
# ===================================================================================
# ANALOGY: You order a coffee (2 mins) and a sandwich (3 mins) at the same time. You get
# everything in 3 minutes, not 5. `asyncio.gather` does this for I/O tasks, running
# them all at once to save a significant amount of time.

async def fetch_menu(restaurant_id: str):
    """Simulates fetching the menu from a database (takes 2 seconds)."""
    print(f"Fetching menu for {restaurant_id}...")
    await asyncio.sleep(2)
    # Return menu from our expanded fake database
    return {"menu": fake_db["menus"].get(restaurant_id, ["No items available"])}

async def fetch_reviews(restaurant_id: str):
    """Simulates fetching reviews from another service (takes 5 seconds)."""
    print(f"Fetching reviews for {restaurant_id}...")
    await asyncio.sleep(5)
    return {"reviews": ["'Amazing food!'", "'A bit spicy for me.'"]}

# Individual endpoints for separate menu and review fetching
@app.get("/restaurants/{restaurant_id}/menu")
async def get_restaurant_menu(restaurant_id: str):
    """Get just the menu for a restaurant (faster endpoint)."""
    return await fetch_menu(restaurant_id)

@app.get("/restaurants/{restaurant_id}/reviews")
async def get_restaurant_reviews(restaurant_id: str):
    """Get just the reviews for a restaurant (slower endpoint)."""
    return await fetch_reviews(restaurant_id)

@app.get("/restaurants/{restaurant_id}/full-details")
async def get_full_restaurant_details(restaurant_id: str):
    """
    Runs two I/O-bound tasks concurrently to fetch all restaurant details.
    Total time is ~5s (the longest task), not 6s.
    """
    print(f"Fetching full details for restaurant {restaurant_id}...")
    # We start both tasks and then use `gather` to wait for both to complete.
    menu_task = fetch_menu(restaurant_id)
    reviews_task = fetch_reviews(restaurant_id)
    # `await` here waits for both tasks to finish.
    menu, reviews = await asyncio.gather(menu_task, reviews_task)
    return {"info": fake_db["restaurants"].get(restaurant_id), **menu, **reviews}


# ===================================================================================
# FEATURE 3: Background Tasks (The Online Shopping Experience)
# ===================================================================================
# ANALOGY: You place an order online and instantly get an "Order Confirmed" message.
# The company handles payment processing and shipping later, in the background.
# You don't have to wait. That's what `BackgroundTasks` does.

async def process_payment_and_notify_kitchen(order_id: str, amount: float):
    """
    A background task that simulates processing a payment and notifying the kitchen.
    This runs *after* the user gets their response.
    """
    print(f"BACKGROUND: Processing payment for order {order_id}...")
    await asyncio.sleep(2)  # Simulate payment gateway
    print(f"BACKGROUND: Payment of ${amount} for order {order_id} successful.")
    fake_db["orders"][order_id]["payment_status"] = "paid"
    print(f"BACKGROUND: Notifying kitchen for order {order_id}...")
    await asyncio.sleep(1) # Simulate sending order to kitchen's system
    print(f"BACKGROUND: Kitchen Acknowledged order {order_id}.")
    fake_db["orders"][order_id]["kitchen_status"] = "acknowledged"

@app.post("/order")
async def place_order(restaurant_id: str, item: str, background_tasks: BackgroundTasks):
    """
    Places an order and schedules payment/kitchen notification to run in the background.
    The user gets an immediate response.
    """
    order_id = f"order_{random.randint(1000, 9999)}"
    order_details = {
        "id": order_id,
        "item": item,
        "status": "order_placed",
        "restaurant": restaurant_id,
    }
    fake_db["orders"][order_id] = order_details
    # This is the "fire-and-forget" part. The user won't wait for this to finish.
    background_tasks.add_task(process_payment_and_notify_kitchen, order_id, 15.50)
    return {"message": "Order placed successfully!", "order_id": order_id}


# ===================================================================================
# FEATURE 4: Streaming Responses (The Live News Ticker / Order Tracker)
# ===================================================================================
# ANALOGY: A live order tracker page. The server continuously pushes updates to your
# phone (e.g., "Preparing" -> "Out for Delivery"). It's a one-way stream of information.
# This is perfect for Server-Sent Events (SSE).

@app.get("/order/{order_id}/live-status", response_class=StreamingResponse)
async def stream_order_status(order_id: str):
    """
    Streams the live status of an order using Server-Sent Events (SSE).
    """
    async def event_generator():
        # A sequence of possible order statuses.
        statuses = ["preparing_food", "quality_check", "out_for_delivery", "delivered"]
        for status in statuses:
            # Update the order status in our fake DB.
            if order_id in fake_db["orders"]:
                fake_db["orders"][order_id]["status"] = status
                event_data = {
                    "order_id": order_id,
                    "status": status,
                    "timestamp": datetime.now().isoformat()
                }
                # `yield` sends a data chunk. SSE format is "data: {json}\n\n".
                yield f"data: {json.dumps(event_data)}\n\n"
                # Wait for a random time before the next status update.
                await asyncio.sleep(random.uniform(2, 8))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ===================================================================================
# FEATURE 5: WebSockets (The Phone Call / Support Chat)
# ===================================================================================
# ANALOGY: A phone call with your delivery driver. Both of you can speak and listen
# at any time. This real-time, two-way communication is exactly what WebSockets are for.

class ConnectionManager:
    """Manages WebSocket connections for a single chat room."""
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

# We create one global manager for our single, mock chat room.
manager = ConnectionManager()

@app.websocket("/ws/support-chat")
async def websocket_support_chat(websocket: WebSocket):
    """A simplified WebSocket endpoint for a mock support chat."""
    await manager.connect(websocket)
    await manager.broadcast("A new user has joined the mock chat.")
    try:
        while True:
            # Wait for a message from a client.
            data = await websocket.receive_text()
            # Broadcast the message to everyone in the chat room.
            # The format is expected to be "username|message|color"
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A user has left the chat.")


# ===================================================================================
# Demo HTML Page
# ===================================================================================
@app.get("/", response_class=FileResponse)
def read_index():
    """Serves the main HTML page for the demo."""
    return "index.html"

# To run this file:
# 1. Make sure you have fastapi and uvicorn installed:
#    pip install "fastapi[all]"
# 2. Run the server:
#    uvicorn main:app --reload