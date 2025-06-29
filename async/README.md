# 🚀 Section 7: FastAPI Async Showcase

This section provides a single, cohesive example to demonstrate FastAPI's core asynchronous features. We use a simple "Live Status Dashboard" concept, explained with real-world analogies, to tie everything together.

## 🎯 What You'll Learn

This example connects the following concepts using analogies:

-   **The Skilled Waiter** (`async def`): How to handle requests efficiently without blocking.
-   **Ordering Coffee & A Sandwich** (`asyncio.gather`): How to run multiple tasks concurrently to save time.
-   **The Online Shopping Experience** (`BackgroundTasks`): How to run "fire-and-forget" jobs after a response is sent.
-   **The Live News Ticker** (`StreamingResponse`): How to push a one-way stream of data from the server.
-   **The Phone Call** (`WebSocket`): How to enable real-time, two-way communication.

---

## 🛠️ Running The Demo

1.  **Navigate to the directory:**
    ```bash
    cd async
    ```

2.  **Install dependencies:**
    ```bash
    pip install "fastapi[all]"
    ```

3.  **Run the FastAPI server:**
    ```bash
    uvicorn main:app --reload
    ```

4.  **Open the demo page:**
    Visit **[http://localhost:8000](http://localhost:8000)** in your browser. This page demonstrates the live streaming and WebSocket features.

---

## 💻 Exploring the Features with Analogies

All features are explained with detailed, line-by-line comments in `main.py`. Here's a quick guide with the analogies.

### 1. Basic Async Endpoint: The Skilled Waiter
-   **Analogy**: A normal waiter takes an order, goes to the kitchen, and waits. An `async` waiter takes the order, gives it to the kitchen, and immediately serves other tables while the food cooks. This is far more efficient.
-   **Concept**: An `async` function allows the server to handle other requests while waiting for a slow I/O operation (like a database call) to complete.
-   **Code Block**:
    ```python
    @app.get("/restaurants/{restaurant_id}")
    async def get_restaurant_info(restaurant_id: str):
        """
        A basic async endpoint to fetch restaurant details.
        Simulates a non-blocking database call.
        """
        print(f"Fetching details for restaurant {restaurant_id}...")
        # `await asyncio.sleep(0.5)` simulates a database query.
        # While "waiting", the server can handle other requests.
        await asyncio.sleep(0.5)
        return fake_db["restaurants"].get(restaurant_id, {"error": "Restaurant not found"})
    ```
-   **Try it**: Visit [http://localhost:8000/status](http://localhost:8000/status).

### 2. Concurrent Tasks: Ordering Coffee & A Sandwich
-   **Analogy**: Instead of ordering and waiting for coffee (2 mins) and *then* ordering and waiting for a sandwich (3 mins) for a total of 5 mins, you order both at once. You get everything in 3 minutes (the time of the longest task).
-   **Concept**: `asyncio.gather` runs multiple slow operations at the same time. The total wait time is determined by the *longest* task, not the sum of all tasks.
-   **Code Block**:
    ```python
    async def fetch_menu(restaurant_id: str):
        """Simulates fetching the menu from a database (takes 1 second)."""
        print(f"Fetching menu for {restaurant_id}...")
        await asyncio.sleep(1)
        return {"menu": ["Curry", "Naan", "Samosa"]}

    async def fetch_reviews(restaurant_id: str):
        """Simulates fetching reviews from another service (takes 1.5 seconds)."""
        print(f"Fetching reviews for {restaurant_id}...")
        await asyncio.sleep(1.5)
        return {"reviews": ["'Amazing food!'", "'A bit spicy for me.'"]}

    @app.get("/restaurants/{restaurant_id}/full-details")
    async def get_full_restaurant_details(restaurant_id: str):
        """
        Runs two I/O-bound tasks concurrently to fetch all restaurant details.
        Total time is ~1.5s (the longest task), not 2.5s.
        """
        print(f"Fetching full details for restaurant {restaurant_id}...")
        # We start both tasks and then use `gather` to wait for both to complete.
        menu_task = fetch_menu(restaurant_id)
        reviews_task = fetch_reviews(restaurant_id)
        # `await` here waits for both tasks to finish.
        menu, reviews = await asyncio.gather(menu_task, reviews_task)
        return {"info": fake_db["restaurants"].get(restaurant_id), **menu, **reviews}
    ```
-   **Try it**: Visit [http://localhost:8000/users/123/dashboard](http://localhost:8000/users/123/dashboard). Check your terminal to see the tasks running in parallel.

### 3. Background Tasks: The Online Shopping Experience
-   **Analogy**: You place an order online and get an "Order Confirmed" message instantly. The company handles the actual packing and shipping later, in the background. You don't have to wait on the website for that to finish.
-   **Concept**: This lets you run a "fire-and-forget" task after sending a response to the user.
-   **Code Block**:
    ```python
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
    ```
-   **How to test**: Keep the [http://localhost:8000](http://localhost:8000) page open. In a new tab, visit the API docs for the "POST" endpoint [here](http://localhost:8000/docs#/default/add_update_and_broadcast_new_update_and_broadcast_post). Click "Try it out", enter a message, and click "Execute". You'll get an immediate response. Switch back to the home page tab. After a 3-second delay, you'll see the background task complete by broadcasting a message to the "Live Update Feed".

### 4. Streaming Responses (SSE): The Live News Ticker
-   **Analogy**: A news station continuously pushes live headlines to your TV screen. It's a one-way stream of information that you just receive.
-   **Concept**: Server-Sent Events (SSE) allow the server to push a continuous stream of data to the client over a single HTTP connection.
-   **Code Block**:
    ```python
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
                    await asyncio.sleep(random.uniform(2, 4))

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    ```
-   **Try it**: Watch the "Live System Monitor" on the homepage. It receives a new update from the server every second.

### 5. WebSockets: The Phone Call
-   **Analogy**: Unlike the one-way news ticker, a phone call is a two-way street. Both people can talk and listen at any time. This is what WebSockets enable.
-   **Concept**: WebSockets provide a persistent, two-way communication channel between the client and server, perfect for real-time chat.
-   **Code Block**:
    ```python
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
                await manager.broadcast(f"Message: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            await manager.broadcast("A user has left the chat.")
    ```
-   **Try it**: Open the homepage in two separate browser windows. Use the "Live Update Feed" chat box to send messages from one window and watch them appear instantly in the other. 