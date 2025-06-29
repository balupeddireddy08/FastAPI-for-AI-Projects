# 🤖 Section 10: AI Integration - Jarvis AI Personal Assistant Platform

Master **AI integration** by building an intelligent personal assistant! Learn how to integrate LangChain, Google Gemini, vector databases, and AI agents to create a powerful AI-driven platform using FastAPI.

## 🎯 What You'll Learn

- LangChain integration for AI workflows
- Google Gemini API for language models
- Vector databases for semantic search
- AI agent creation and tool usage
- Streaming AI responses and conversation memory

## 🤖 Meet Jarvis AI Platform

Our AI assistant demonstrates cutting-edge integration through:

**Key Features:**
- 💬 Conversational AI with memory
- 📚 Document Q&A and knowledge retrieval
- 🛠️ AI agents with custom tools
- 🔍 Semantic search across documents
- ⚡ Streaming responses and real-time chat

## 🚀 Core AI Integration Concepts

### **1. LangChain Setup and Models**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from fastapi import FastAPI
import os

app = FastAPI(title="🤖 Jarvis AI Platform")

# Initialize Google Gemini model
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,
    convert_system_message_to_human=True
)

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_memory: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    sources: Optional[List[str]] = None

@app.post("/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Basic AI chat with conversation memory"""
    
    # Create conversation memory
    memory = ConversationBufferMemory(return_messages=True)
    
    # Load previous conversation if exists
    if request.conversation_id and request.use_memory:
        previous_messages = load_conversation(request.conversation_id)
        for msg in previous_messages:
            memory.chat_memory.add_message(msg)
    
    # Add current message to memory
    memory.chat_memory.add_user_message(request.message)
    
    # Get AI response
    messages = memory.chat_memory.messages
    response = await llm.ainvoke(messages)
    
    # Add AI response to memory
    memory.chat_memory.add_ai_message(response.content)
    
    # Save conversation
    conversation_id = request.conversation_id or generate_conversation_id()
    save_conversation(conversation_id, memory.chat_memory.messages)
    
    return ChatResponse(
        response=response.content,
        conversation_id=conversation_id
    )
```

### **2. Document Q&A with Vector Search**

```python
from langchain.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

# Initialize embeddings and vector store
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

class DocumentUpload(BaseModel):
    title: str
    description: Optional[str] = None

class DocumentQuestion(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None

@app.post("/ai/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    metadata: DocumentUpload = Depends()
):
    """Upload and process document for Q&A"""
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Load and split document
    if file.filename.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    documents = loader.load()
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Add metadata
    for chunk in chunks:
        chunk.metadata.update({
            "title": metadata.title,
            "description": metadata.description,
            "filename": file.filename
        })
    
    # Add to vector store
    document_ids = vector_store.add_documents(chunks)
    
    return {
        "message": "Document uploaded and processed",
        "document_ids": document_ids,
        "chunks_created": len(chunks)
    }

@app.post("/ai/ask-document")
async def ask_document(request: DocumentQuestion):
    """Ask questions about uploaded documents"""
    
    # Create retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
        return_source_documents=True
    )
    
    # Get answer
    result = qa_chain({"query": request.question})
    
    # Extract sources
    sources = [doc.metadata.get("title", "Unknown") for doc in result["source_documents"]]
    
    return ChatResponse(
        response=result["result"],
        conversation_id=generate_conversation_id(),
        sources=list(set(sources))
    )
```

### **3. AI Agents with Tools**

```python
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain import hub
import requests
import json

class WeatherTool(BaseTool):
    name = "weather"
    description = "Get current weather information for a city"
    
    def _run(self, city: str) -> str:
        # Mock weather API call
        api_key = "your-weather-api-key"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                return f"Weather in {city}: {data['weather'][0]['description']}, Temperature: {data['main']['temp']}°K"
            else:
                return f"Could not get weather for {city}"
        except:
            return "Weather service unavailable"

class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Perform mathematical calculations"
    
    def _run(self, expression: str) -> str:
        try:
            # Safe evaluation of mathematical expressions
            result = eval(expression, {"__builtins__": {}}, {
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow, "sqrt": lambda x: x**0.5
            })
            return f"Result: {result}"
        except:
            return "Invalid mathematical expression"

# Initialize tools and agent
tools = [WeatherTool(), CalculatorTool()]

# Get ReAct prompt template
prompt = hub.pull("hwchase17/react")

# Create agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

class AgentRequest(BaseModel):
    task: str
    max_iterations: int = 5

@app.post("/ai/agent")
async def run_agent(request: AgentRequest):
    """Run AI agent with access to tools"""
    
    try:
        result = agent_executor.invoke({
            "input": request.task,
            "max_iterations": request.max_iterations
        })
        
        return {
            "result": result["output"],
            "intermediate_steps": result.get("intermediate_steps", [])
        }
    except Exception as e:
        return {"error": str(e), "result": "Agent execution failed"}
```

## 🔗 Streaming AI Responses

### **1. Streaming Chat with Server-Sent Events**

```python
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/ai/chat-stream")
async def stream_chat(request: ChatRequest):
    """Stream AI responses in real-time"""
    
    async def generate_response():
        memory = ConversationBufferMemory(return_messages=True)
        
        # Load conversation history
        if request.conversation_id:
            previous_messages = load_conversation(request.conversation_id)
            for msg in previous_messages:
                memory.chat_memory.add_message(msg)
        
        memory.chat_memory.add_user_message(request.message)
        
        # Stream the response
        response_text = ""
        async for chunk in llm.astream(memory.chat_memory.messages):
            if chunk.content:
                response_text += chunk.content
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.content})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'complete', 'full_response': response_text})}\n\n"
        
        # Save conversation
        memory.chat_memory.add_ai_message(response_text)
        conversation_id = request.conversation_id or generate_conversation_id()
        save_conversation(conversation_id, memory.chat_memory.messages)
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### **2. WebSocket Chat Interface**

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

class ChatManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.conversations: Dict[str, ConversationBufferMemory] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.conversations[client_id] = ConversationBufferMemory(return_messages=True)

    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.conversations:
            del self.conversations[client_id]

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

chat_manager = ChatManager()

@app.websocket("/ai/ws-chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    await chat_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data["message"]
            
            # Add to conversation memory
            memory = chat_manager.conversations[client_id]
            memory.chat_memory.add_user_message(user_message)
            
            # Send typing indicator
            await chat_manager.send_message(client_id, {"type": "typing", "status": True})
            
            # Generate AI response
            response = await llm.ainvoke(memory.chat_memory.messages)
            memory.chat_memory.add_ai_message(response.content)
            
            # Send response
            await chat_manager.send_message(client_id, {
                "type": "message",
                "content": response.content,
                "sender": "assistant"
            })
            
    except WebSocketDisconnect:
        await chat_manager.disconnect(client_id)
```

## 📊 Advanced AI Features

### **1. Conversation Analytics**

```python
from langchain.chains.summarize import load_summarize_chain

@app.get("/ai/conversation/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str):
    """Generate summary of conversation"""
    
    messages = load_conversation(conversation_id)
    
    # Convert messages to documents for summarization
    docs = [
        Document(page_content=f"{msg.type}: {msg.content}")
        for msg in messages
    ]
    
    # Generate summary
    summary_chain = load_summarize_chain(llm, chain_type="stuff")
    summary = summary_chain.run(docs)
    
    return {"summary": summary, "message_count": len(messages)}

@app.get("/ai/conversation/{conversation_id}/analytics")
async def get_conversation_analytics(conversation_id: str):
    """Get detailed conversation analytics"""
    
    messages = load_conversation(conversation_id)
    
    user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
    
    # Calculate metrics
    avg_user_length = sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0
    avg_ai_length = sum(len(msg.content) for msg in ai_messages) / len(ai_messages) if ai_messages else 0
    
    return {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "ai_messages": len(ai_messages),
        "avg_user_message_length": round(avg_user_length, 2),
        "avg_ai_message_length": round(avg_ai_length, 2),
        "conversation_start": messages[0].timestamp if messages else None
    }
```

## 🎮 Key AI Endpoints

### **Core Chat Features**
```python
@app.post("/ai/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest)

@app.post("/ai/chat-stream")
async def stream_chat(request: ChatRequest)

@app.websocket("/ai/ws-chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str)
```

### **Document Intelligence**
```python
@app.post("/ai/upload-document")
async def upload_document(file: UploadFile = File(...))

@app.post("/ai/ask-document")
async def ask_document(request: DocumentQuestion)

@app.get("/ai/documents")
async def list_documents()
```

### **AI Agents & Tools**
```python
@app.post("/ai/agent")
async def run_agent(request: AgentRequest)

@app.get("/ai/tools")
async def list_available_tools()

@app.post("/ai/tools/custom")
async def create_custom_tool(tool_definition: ToolDefinition)
```

## 🛠️ Running Jarvis AI

```bash
cd 10-ai-integration
pip install langchain langchain-google-genai chromadb
uvicorn main:app --reload

# Test AI features:
# POST /ai/chat (basic chat)
# POST /ai/chat-stream (streaming responses)
# POST /ai/upload-document (document Q&A)
# WebSocket: ws://localhost:8000/ai/ws-chat/user123
```

## 📊 AI Integration Architecture

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language Model** | Google Gemini Pro | Core AI reasoning |
| **Vector Database** | ChromaDB | Document embeddings |
| **Memory** | LangChain Memory | Conversation context |
| **Agents** | LangChain Agents | Tool-based AI actions |
| **Streaming** | FastAPI SSE/WebSocket | Real-time responses |

## 🎮 Practice Exercises

1. **🧠 Custom AI Agent**: Build agent with web search and API tools
2. **📚 Knowledge Base**: Create domain-specific document Q&A system
3. **🎯 AI Workflows**: Implement multi-step AI task automation
4. **📊 Analytics Dashboard**: Build AI conversation insights panel

## 💡 AI Integration Best Practices

### **Performance Optimization**
- Use streaming for better user experience
- Implement conversation memory efficiently
- Cache embeddings and frequent responses
- Optimize vector search parameters

### **Security & Privacy**
- Sanitize all user inputs before AI processing
- Implement rate limiting for AI endpoints
- Secure API keys with environment variables
- Add conversation data encryption

### **User Experience**
- Provide typing indicators during processing
- Show conversation context and sources
- Enable conversation history and export
- Add fallback responses for AI failures

## 🚀 Next Steps

Congratulations! You've completed the entire FastAPI tutorial series. You now have the skills to build:

- **Scalable APIs** with proper architecture
- **Real-time features** with WebSockets and streaming
- **Secure systems** with enterprise-grade authentication
- **AI-powered applications** with modern language models

**Key Takeaway**: AI integration opens up unlimited possibilities - from simple chatbots to complex reasoning systems. The future is AI-powered, and you're ready to build it! 🤖✨

## 🎉 Tutorial Complete!

You've mastered all 10 sections of FastAPI development:
1. ☕ **Introduction** - Coffee Shop API
2. 🎮 **Type Hints** - Game Character Builder  
3. 👨‍🍳 **Pydantic** - Recipe Validation
4. 📚 **Routing** - Digital Library
5. 📱 **Request/Response** - Social Media Platform
6. 📚 **Documentation** - AI Assistant Marketplace
7. 🎮 **Async** - Real-time Gaming Platform
8. 🎬 **Streaming** - Live Content Platform
9. 🏦 **Security** - Digital Banking System
10. 🤖 **AI Integration** - Personal Assistant Platform

**You're now ready to build world-class APIs with FastAPI!** 🚀 