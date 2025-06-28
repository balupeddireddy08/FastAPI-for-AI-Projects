# Asynchronous Programming in FastAPI

FastAPI is built on top of Starlette and leverages Python's asynchronous capabilities to handle many concurrent requests efficiently. Understanding asynchronous programming is essential for building high-performance APIs.

## What is Asynchronous Programming?

Asynchronous programming allows operations to run concurrently without blocking the main thread. This is especially useful for I/O-bound operations like:
- Database queries
- API calls to external services
- File operations
- Network operations

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Handler1
    participant Database
    participant ExternalAPI
    
    Client->>Server: Request A
    Server->>Handler1: Process Request A
    
    Client->>Server: Request B
    Note over Server: Don't wait for Request A to complete
    Server->>Handler1: Process Request B
    
    Handler1->>Database: Query for Request A
    Handler1->>ExternalAPI: API call for Request B
    
    Database-->>Handler1: Database Results
    ExternalAPI-->>Handler1: API Results
    
    Handler1-->>Server: Response for Request A
    Handler1-->>Server: Response for Request B
    
    Server-->>Client: Response A
    Server-->>Client: Response B
```

## Synchronous vs. Asynchronous

### Synchronous (Blocking)

```mermaid
graph LR
    A[Request 1] -->|Process| B[Request 1 Complete]
    B -->|Start| C[Request 2]
    C -->|Process| D[Request 2 Complete]
    D -->|Start| E[Request 3]
    E -->|Process| F[Request 3 Complete]
```

### Asynchronous (Non-Blocking)

```mermaid
graph LR
    A[Request 1] -->|Start| B[Request 1 Processing]
    A -->|Also Start| C[Request 2 Processing]
    A -->|Also Start| D[Request 3 Processing]
    B --> E[Request 1 Complete]
    C --> F[Request 2 Complete]
    D --> G[Request 3 Complete]
```

## Async/Await in Python

Modern Python (3.5+) provides `async` and `await` keywords for asynchronous programming:

- `async def`: Defines a coroutine function
- `await`: Pauses execution until the awaited coroutine completes

```python
import asyncio

async def fetch_data():
    print("Start fetching")
    await asyncio.sleep(2)  # Simulate I/O operation
    print("Done fetching")
    return {"data": 42}

async def main():
    data = await fetch_data()
    print(data)

asyncio.run(main())
```

## FastAPI and Async

FastAPI allows you to use both synchronous and asynchronous path operation functions:

### Synchronous
```python
@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}
```

### Asynchronous
```python
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

## When to Use Async in FastAPI

Use `async def` when:
- Making network calls
- Making database queries
- Performing I/O operations
- Calling other asynchronous functions

Use normal `def` when:
- CPU-bound operations
- Calling synchronous-only libraries
- No I/O or external calls are made

## Working with Async Database Clients

Example with async database client:

```python
from fastapi import FastAPI, Depends
from databases import Database

app = FastAPI()
database = Database("postgresql://user:password@localhost/db")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = :user_id"
    user = await database.fetch_one(query=query, values={"user_id": user_id})
    if user:
        return user
    return {"error": "User not found"}
```

## Making Async HTTP Requests

Use libraries like `httpx` for async HTTP requests:

```python
import httpx
from fastapi import FastAPI

app = FastAPI()

@app.get("/proxy/{item_id}")
async def proxy_request(item_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/items/{item_id}")
        data = response.json()
        return data
```

## Handling Multiple Async Operations

You can execute multiple async operations concurrently:

```python
import asyncio
import httpx
from fastapi import FastAPI

app = FastAPI()

async def fetch_resource(client, url):
    response = await client.get(url)
    return response.json()

@app.get("/dashboard/")
async def get_dashboard():
    async with httpx.AsyncClient() as client:
        # Execute three API calls concurrently
        tasks = [
            fetch_resource(client, "https://api.example.com/users"),
            fetch_resource(client, "https://api.example.com/products"),
            fetch_resource(client, "https://api.example.com/sales"),
        ]
        users, products, sales = await asyncio.gather(*tasks)
        
        return {
            "users": users,
            "products": products,
            "sales": sales,
        }
```

## Background Tasks

FastAPI provides a `BackgroundTasks` class for executing operations after returning a response:

```python
from fastapi import FastAPI, BackgroundTasks

app = FastAPI()

def process_item(item_id):
    # This runs in the background after response is sent
    print(f"Processing item {item_id}")
    # ...lengthy operation...

@app.post("/items/{item_id}")
async def create_item(item_id: int, background_tasks: BackgroundTasks):
    # Schedule the function to run in the background
    background_tasks.add_task(process_item, item_id)
    return {"message": "Item received"}
```

## Common Pitfalls

### 1. Blocking the Event Loop

Be careful not to block the event loop with CPU-intensive tasks:

```python
# Bad: This blocks the event loop
@app.get("/fibonacci/{n}")
async def bad_fibonacci(n: int):
    if n <= 1:
        return n
    return bad_fibonacci(n-1) + bad_fibonacci(n-2)
```

Solution: Use a thread pool for CPU-bound tasks:

```python
from fastapi import FastAPI
import asyncio
from functools import partial
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()
process_executor = ProcessPoolExecutor()

def cpu_bound_task(n):
    # CPU-intensive task
    if n <= 1:
        return n
    return cpu_bound_task(n-1) + cpu_bound_task(n-2)

@app.get("/fibonacci/{n}")
async def good_fibonacci(n: int):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        process_executor,
        partial(cpu_bound_task, n)
    )
    return result
```

### 2. Mixing Sync and Async

Be careful when calling sync functions from async functions:

```python
# This could block the event loop
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    # Blocking I/O operation
    with open("log.txt", "a") as f:
        f.write(f"Access to item {item_id}\n")
    return {"item_id": item_id}
```

Solution: Use `run_in_executor`:

```python
import asyncio
from functools import partial

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    loop = asyncio.get_event_loop()
    
    def write_log(item_id):
        with open("log.txt", "a") as f:
            f.write(f"Access to item {item_id}\n")
    
    await loop.run_in_executor(None, partial(write_log, item_id))
    return {"item_id": item_id}
```

### 3. Not Using Async Database Clients

If using a database, prefer async clients:

- **SQLAlchemy**: Use SQLAlchemy 1.4+ with its async features
- **MongoDB**: Use Motor instead of PyMongo
- **PostgreSQL**: Use asyncpg
- **Generic**: Use databases package

## Async Dependencies in FastAPI

You can use async functions as dependencies:

```python
from fastapi import Depends, FastAPI

app = FastAPI()

async def get_db():
    db = await connect_to_db()
    try:
        yield db
    finally:
        await db.close()

@app.get("/items/")
async def read_items(db=Depends(get_db)):
    return await db.fetch_all("SELECT * FROM items")
```

## Working with WebSockets

FastAPI provides support for WebSockets:

```python
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
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

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received: {data}")
```

## Testing Async Code

You can test async code with pytest and its asyncio support:

```python
import pytest
from httpx import AsyncClient
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": "Test Item"}

@pytest.mark.asyncio
async def test_read_item():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/items/42")
        assert response.status_code == 200
        assert response.json() == {"item_id": 42, "name": "Test Item"}
```

## Performance Benefits

Using async in FastAPI can provide significant performance benefits:

```mermaid
graph LR
    A[FastAPI with async] -->|Higher throughput| B[Handle more requests]
    A -->|Lower latency| C[Faster response times]
    A -->|Efficient resource usage| D[Lower memory usage]
```

1. **Concurrency without threads**: Handle many connections with limited resources
2. **Reduced idle time**: Make progress on other requests while waiting for I/O
3. **Improved throughput**: Serve more requests per second
4. **Better responsiveness**: Keep the application responsive under load

## Converting from Sync to Async

When converting a synchronous FastAPI application to async:

1. Change function definitions from `def` to `async def`
2. Add `await` before calls to async functions
3. Replace synchronous libraries with asynchronous alternatives
4. Use `run_in_executor` for unavoidable synchronous code
5. Test thoroughly to ensure performance benefits

## Next Steps

In the next section, we'll explore streaming responses in FastAPI, which builds on asynchronous programming to provide real-time data to clients.

## Practice Exercise

Create a FastAPI application that:

1. Has an endpoint that fetches data from multiple external APIs concurrently
2. Includes a background task that processes data after returning a response
3. Implements a WebSocket endpoint for real-time updates 