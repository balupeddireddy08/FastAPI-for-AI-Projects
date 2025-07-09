import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, validator
from enum import Enum
import tempfile

# LangChain imports
from langchain.llms import GooglePalm
from langchain.chat_models import ChatGooglePalm
from langchain.embeddings import GooglePalmEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.tools import BaseTool
from langchain.callbacks.base import BaseCallbackHandler
from fastapi.responses import HTMLResponse

# Google AI imports  
import google.generativeai as genai

# Initialize Jarvis - Your AI Personal Assistant Platform
app = FastAPI(
    title="🤖 Jarvis AI - Personal Assistant Platform",
    description="""
    Welcome to **Jarvis AI** - the most advanced personal assistant platform! 🚀✨
    
    Powered by cutting-edge AI technology including:
    
    * 🧠 **Google Gemini**: State-of-the-art language understanding
    * 🔗 **LangChain Integration**: Advanced AI workflow orchestration  
    * 📚 **Document Intelligence**: Upload and chat with your documents
    * 💭 **Conversation Memory**: Contextual discussions that remember everything
    * 🛠️ **AI Tools & Agents**: Autonomous task execution and problem solving
    * 🎯 **Personalized Responses**: AI that learns your preferences and style
    * 📊 **Data Analysis**: Intelligent insights from your data
    * 🌍 **Multi-modal AI**: Text, images, and document processing
    
    Built with FastAPI + LangChain + Gemini - Your personal AI genius! 🧠
    """,
    version="1.0.0"
)

# === AI CONFIGURATION ===

# Set up API keys (in production, use environment variables)
os.environ["GOOGLE_API_KEY"] = "your-google-api-key-here"  # Replace with actual key
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Initialize AI models
try:
    # Gemini Pro for general conversations
    gemini_model = genai.GenerativeModel('gemini-pro')
    
    # LangChain integration with Google Palm
    llm = ChatGooglePalm(
        model_name="models/chat-bison-001",
        temperature=0.7,
        max_output_tokens=1024
    )
    
    # Embeddings for document processing
    embeddings = GooglePalmEmbeddings()
    
    print("✅ AI models initialized successfully!")
    
except Exception as e:
    print(f"⚠️ AI model initialization failed: {e}")
    print("🔧 Using mock responses for demo purposes")
    llm = None
    embeddings = None

# === AI MODELS & TYPES ===

class AssistantPersonality(str, Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    WITTY = "witty"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    JARVIS = "jarvis"  # Iron Man style!

class TaskType(str, Enum):
    CHAT = "chat"
    DOCUMENT_QA = "document_qa"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    CREATIVE_WRITING = "creative_writing"
    RESEARCH = "research"
    PLANNING = "planning"

class ConversationMode(str, Enum):
    CASUAL = "casual"
    FOCUS = "focus"
    RESEARCH = "research"
    CREATIVE = "creative"
    PROBLEM_SOLVING = "problem_solving"

# === REQUEST/RESPONSE MODELS ===

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, max_length=8000, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000, description="Your message to Jarvis")
    conversation_id: Optional[str] = Field(None, description="Conversation ID to continue existing chat")
    personality: AssistantPersonality = Field(AssistantPersonality.JARVIS, description="AI personality style")
    mode: ConversationMode = Field(ConversationMode.CASUAL, description="Conversation mode")
    context: Optional[str] = Field(None, max_length=2000, description="Additional context for the conversation")
    use_memory: bool = Field(True, description="Whether to use conversation memory")

class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int
    document_id: str
    chunks_processed: int
    embedding_status: str

class AITaskRequest(BaseModel):
    task_type: TaskType = Field(..., description="Type of AI task to perform")
    description: str = Field(..., min_length=1, max_length=2000, description="Detailed task description")
    context_documents: Optional[List[str]] = Field([], description="Document IDs to use as context")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Task-specific parameters")
    priority: int = Field(5, ge=1, le=10, description="Task priority (1=lowest, 10=highest)")

class ConversationResponse(BaseModel):
    conversation_id: str
    message: str
    personality: str
    thinking_process: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: Optional[List[str]] = []
    suggested_actions: Optional[List[str]] = []
    timestamp: datetime

# === GLOBAL AI STATE ===

# Conversation storage
conversations: Dict[str, Dict] = {}
conversation_memories: Dict[str, ConversationBufferWindowMemory] = {}
document_store: Dict[str, Any] = {}  # Document embeddings and metadata
active_tasks: Dict[str, Dict] = {}  # Background AI tasks

# === CUSTOM LANGCHAIN TOOLS ===

class CalculatorTool(BaseTool):
    """Custom tool for mathematical calculations"""
    name = "calculator"
    description = "Useful for mathematical calculations and computations"
    
    def _run(self, expression: str) -> str:
        try:
            # Safe evaluation of mathematical expressions
            allowed_names = {
                k: v for k, v in __builtins__.items() 
                if k in ['abs', 'round', 'min', 'max', 'sum', 'pow']
            }
            allowed_names.update({'__builtins__': {}})
            
            result = eval(expression, allowed_names)
            return f"The result of {expression} is {result}"
        except Exception as e:
            return f"Error in calculation: {str(e)}"
    
    async def _arun(self, expression: str) -> str:
        return self._run(expression)

class WebSearchTool(BaseTool):
    """Mock web search tool (in production, integrate with real search API)"""
    name = "web_search"
    description = "Search the web for current information"
    
    def _run(self, query: str) -> str:
        # Mock search results
        return f"Here are some search results for '{query}': [Mock results - integrate with real search API]"
    
    async def _arun(self, query: str) -> str:
        return self._run(query)

class WeatherTool(BaseTool):
    """Mock weather tool (integrate with real weather API)"""
    name = "weather"
    description = "Get current weather information for a location"
    
    def _run(self, location: str) -> str:
        # Mock weather data
        return f"Current weather in {location}: 72°F, Partly cloudy with light breeze. Perfect day!"
    
    async def _arun(self, location: str) -> str:
        return self._run(location)

# Initialize AI tools
ai_tools = [
    CalculatorTool(),
    WebSearchTool(),
    WeatherTool()
]

# === AI UTILITY FUNCTIONS ===

def get_personality_prompt(personality: AssistantPersonality) -> str:
    """Get personality-specific prompts"""
    prompts = {
        AssistantPersonality.PROFESSIONAL: "You are a professional AI assistant. Provide clear, concise, and business-appropriate responses.",
        AssistantPersonality.FRIENDLY: "You are a friendly and approachable AI assistant. Be warm, helpful, and conversational.",
        AssistantPersonality.WITTY: "You are a witty AI assistant with a good sense of humor. Be clever and entertaining while being helpful.",
        AssistantPersonality.TECHNICAL: "You are a technical AI assistant. Provide detailed, accurate technical information and solutions.",
        AssistantPersonality.CREATIVE: "You are a creative AI assistant. Think outside the box and provide imaginative solutions.",
        AssistantPersonality.JARVIS: "You are Jarvis, an advanced AI assistant like from Iron Man. Be sophisticated, intelligent, slightly formal but caring, and always ready to help with any task. Use 'Sir' occasionally and demonstrate advanced problem-solving capabilities."
    }
    return prompts.get(personality, prompts[AssistantPersonality.JARVIS])

def create_conversation_memory(conversation_id: str) -> ConversationBufferWindowMemory:
    """Create conversation memory for context retention"""
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
    return conversation_memories[conversation_id]

async def process_with_gemini(prompt: str, personality: AssistantPersonality) -> Dict[str, Any]:
    """Process request with Google Gemini"""
    try:
        # Add personality to prompt
        personality_prompt = get_personality_prompt(personality)
        full_prompt = f"{personality_prompt}\n\nUser: {prompt}\n\nAssistant:"
        
        if gemini_model:
            response = gemini_model.generate_content(full_prompt)
            return {
                "response": response.text,
                "confidence": 0.9,
                "model": "gemini-pro"
            }
        else:
            # Mock response for demo
            return {
                "response": f"[Mock Gemini Response] Hello! I'm your AI assistant. You asked: '{prompt}'. This is a demonstration response since the API key is not configured.",
                "confidence": 0.8,
                "model": "mock"
            }
    except Exception as e:
        return {
            "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
            "confidence": 0.3,
            "model": "error"
        }

# === MAIN AI ENDPOINTS ===

@app.get("/", response_class=HTMLResponse)
def ai_platform_home():
    """Serves the main HTML page for the Jarvis AI Platform."""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# === CONVERSATION ENDPOINTS ===

@app.post("/chat", response_model=ConversationResponse)
async def chat_with_jarvis(request: ConversationRequest):
    """
    💬 Chat with Jarvis - Your AI Personal Assistant
    
    Have natural conversations with advanced AI that remembers context and provides intelligent responses.
    """
    # Get or create conversation ID
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "created_at": datetime.now(),
            "personality": request.personality,
            "mode": request.mode,
            "messages": []
        }
    
    # Add user message to conversation
    user_message = ChatMessage(
        role="user",
        content=request.message,
        metadata={"personality": request.personality.value, "mode": request.mode.value}
    )
    conversations[conversation_id]["messages"].append(user_message)
    
    # Build conversation context
    context = ""
    if request.context:
        context = f"Additional context: {request.context}\n"
    
    # Add conversation memory
    memory_context = ""
    if request.use_memory and conversation_id in conversation_memories:
        memory = conversation_memories[conversation_id]
        memory_context = f"Previous conversation context: {memory.buffer}\n"
    
    # Create enhanced prompt
    enhanced_prompt = f"""
{context}{memory_context}
Mode: {request.mode.value}
Current message: {request.message}
"""
    
    # Process with AI
    ai_response = await process_with_gemini(enhanced_prompt, request.personality)
    
    # Update conversation memory
    if request.use_memory:
        memory = create_conversation_memory(conversation_id)
        memory.save_context(
            {"input": request.message},
            {"output": ai_response["response"]}
        )
    
    # Create assistant message
    assistant_message = ChatMessage(
        role="assistant",
        content=ai_response["response"],
        metadata={
            "model": ai_response["model"],
            "confidence": ai_response["confidence"]
        }
    )
    conversations[conversation_id]["messages"].append(assistant_message)
    
    # Generate suggested actions based on conversation
    suggested_actions = []
    if "document" in request.message.lower():
        suggested_actions.append("📄 Upload a document for analysis")
    if "code" in request.message.lower():
        suggested_actions.append("💻 Request code generation")
    if "analyze" in request.message.lower():
        suggested_actions.append("📊 Create a data analysis task")
    
    return ConversationResponse(
        conversation_id=conversation_id,
        message=ai_response["response"],
        personality=request.personality.value,
        confidence=ai_response["confidence"],
        suggested_actions=suggested_actions,
        timestamp=datetime.now()
    )

@app.get("/conversations/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """📜 Get conversation history and context"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="🔍 Conversation not found")
    
    conversation = conversations[conversation_id]
    
    return {
        "conversation_id": conversation_id,
        "created_at": conversation["created_at"],
        "personality": conversation["personality"],
        "mode": conversation["mode"],
        "message_count": len(conversation["messages"]),
        "messages": conversation["messages"][-20:],  # Last 20 messages
        "memory_active": conversation_id in conversation_memories
    }

# === DOCUMENT PROCESSING ENDPOINTS ===

@app.post("/documents/upload", response_model=DocumentUpload)
async def upload_document(
    file: UploadFile = File(..., description="Document to upload and process"),
    description: Optional[str] = Form(None, description="Description of the document")
):
    """
    📄 Upload and process documents with AI
    
    Upload PDF, text files, or other documents to create an intelligent knowledge base.
    """
    # Validate file type
    allowed_types = [
        "text/plain", "application/pdf", "text/markdown",
        "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"📄 Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Generate document ID
    document_id = str(uuid.uuid4())
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Process document based on type
        if file.content_type == "application/pdf":
            loader = PyPDFLoader(temp_file_path)
        else:
            loader = TextLoader(temp_file_path)
        
        # Load and split document
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create embeddings if available
        embedding_status = "completed"
        vector_store = None
        
        if embeddings:
            try:
                vector_store = FAISS.from_documents(chunks, embeddings)
                embedding_status = "completed"
            except Exception as e:
                embedding_status = f"failed: {str(e)}"
        else:
            embedding_status = "skipped (demo mode)"
        
        # Store document metadata
        document_store[document_id] = {
            "id": document_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(content),
            "description": description,
            "chunks": chunks,
            "vector_store": vector_store,
            "uploaded_at": datetime.now(),
            "embedding_status": embedding_status
        }
        
        return DocumentUpload(
            filename=file.filename,
            content_type=file.content_type,
            size=len(content),
            document_id=document_id,
            chunks_processed=len(chunks),
            embedding_status=embedding_status
        )
        
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

@app.post("/documents/{document_id}/chat")
async def chat_with_document(
    document_id: str,
    question: str = Form(..., min_length=1, max_length=1000),
    conversation_id: Optional[str] = Form(None)
):
    """
    📚 Chat with your documents
    
    Ask questions about uploaded documents and get intelligent answers with citations.
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="📄 Document not found")
    
    document = document_store[document_id]
    
    if not document["vector_store"]:
        # Fallback: search through text chunks manually
        relevant_chunks = []
        question_lower = question.lower()
        
        for chunk in document["chunks"]:
            if any(word in chunk.page_content.lower() for word in question_lower.split()):
                relevant_chunks.append(chunk.page_content[:500])
        
        context = "\n\n".join(relevant_chunks[:3]) if relevant_chunks else "No relevant content found."
        
        prompt = f"""
        Based on the following document content, answer the question:
        
        Document: {document['filename']}
        Content: {context}
        
        Question: {question}
        
        Please provide a detailed answer based on the document content.
        """
        
        ai_response = await process_with_gemini(prompt, AssistantPersonality.PROFESSIONAL)
        
        return {
            "document_id": document_id,
            "document_name": document["filename"],
            "question": question,
            "answer": ai_response["response"],
            "confidence": ai_response["confidence"],
            "sources": ["Document chunks (manual search)"],
            "timestamp": datetime.now()
        }
    
    else:
        # Use vector store for semantic search
        try:
            retriever = document["vector_store"].as_retriever(search_kwargs={"k": 3})
            
            # Create conversation chain
            memory = create_conversation_memory(conversation_id or document_id)
            
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=True
            )
            
            result = qa_chain({"question": question})
            
            return {
                "document_id": document_id,
                "document_name": document["filename"],
                "question": question,
                "answer": result["answer"],
                "confidence": 0.9,
                "sources": [doc.page_content[:200] + "..." for doc in result["source_documents"]],
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document question: {str(e)}"
            )

@app.get("/documents/")
async def list_documents():
    """📋 List all uploaded documents"""
    documents = []
    for doc_id, doc_data in document_store.items():
        documents.append({
            "document_id": doc_id,
            "filename": doc_data["filename"],
            "size": doc_data["size"],
            "uploaded_at": doc_data["uploaded_at"],
            "embedding_status": doc_data["embedding_status"],
            "chunks_count": len(doc_data["chunks"])
        })
    
    return {
        "total_documents": len(documents),
        "documents": documents
    }

# === AI TASK AUTOMATION ===

@app.post("/tasks/create")
async def create_ai_task(request: AITaskRequest, background_tasks: BackgroundTasks):
    """
    🛠️ Create autonomous AI tasks
    
    Let Jarvis work on complex tasks in the background while you continue with other work.
    """
    task_id = str(uuid.uuid4())
    
    # Store task
    active_tasks[task_id] = {
        "id": task_id,
        "type": request.task_type,
        "description": request.description,
        "status": "queued",
        "created_at": datetime.now(),
        "priority": request.priority,
        "parameters": request.parameters,
        "context_documents": request.context_documents,
        "progress": 0,
        "result": None
    }
    
    # Start background processing
    background_tasks.add_task(process_ai_task, task_id)
    
    return {
        "task_id": task_id,
        "message": f"🚀 AI task '{request.task_type}' created successfully!",
        "description": request.description,
        "status": "queued",
        "estimated_completion": "2-5 minutes",
        "check_status_url": f"/tasks/{task_id}/status"
    }

async def process_ai_task(task_id: str):
    """Background task processor"""
    if task_id not in active_tasks:
        return
    
    task = active_tasks[task_id]
    task["status"] = "processing"
    task["started_at"] = datetime.now()
    
    try:
        # Simulate task processing
        await asyncio.sleep(2)  # Simulate processing time
        task["progress"] = 25
        
        # Process based on task type
        if task["type"] == TaskType.CODE_GENERATION:
            result = await generate_code_task(task)
        elif task["type"] == TaskType.CREATIVE_WRITING:
            result = await creative_writing_task(task)
        elif task["type"] == TaskType.DATA_ANALYSIS:
            result = await data_analysis_task(task)
        elif task["type"] == TaskType.RESEARCH:
            result = await research_task(task)
        else:
            result = await general_ai_task(task)
        
        task["progress"] = 100
        task["status"] = "completed"
        task["result"] = result
        task["completed_at"] = datetime.now()
        
    except Exception as e:
        task["status"] = "failed"
        task["error"] = str(e)
        task["completed_at"] = datetime.now()

async def generate_code_task(task: Dict) -> Dict:
    """Generate code based on task description"""
    prompt = f"""
    Generate clean, well-documented code for the following requirement:
    
    {task['description']}
    
    Include:
    - Clean, readable code
    - Comments explaining key parts
    - Error handling where appropriate
    - Example usage
    """
    
    ai_response = await process_with_gemini(prompt, AssistantPersonality.TECHNICAL)
    
    return {
        "code": ai_response["response"],
        "language": task["parameters"].get("language", "python"),
        "confidence": ai_response["confidence"],
        "notes": "Code generated using AI. Please review before production use."
    }

async def creative_writing_task(task: Dict) -> Dict:
    """Creative writing task"""
    prompt = f"""
    Create engaging creative content for:
    
    {task['description']}
    
    Style: {task['parameters'].get('style', 'engaging and creative')}
    Length: {task['parameters'].get('length', 'medium')}
    
    Make it original, engaging, and well-structured.
    """
    
    ai_response = await process_with_gemini(prompt, AssistantPersonality.CREATIVE)
    
    return {
        "content": ai_response["response"],
        "style": task["parameters"].get("style", "creative"),
        "word_count": len(ai_response["response"].split()),
        "confidence": ai_response["confidence"]
    }

async def data_analysis_task(task: Dict) -> Dict:
    """Data analysis task"""
    prompt = f"""
    Provide detailed data analysis insights for:
    
    {task['description']}
    
    Include:
    - Key patterns and trends
    - Statistical insights
    - Recommendations
    - Potential issues or concerns
    """
    
    ai_response = await process_with_gemini(prompt, AssistantPersonality.TECHNICAL)
    
    return {
        "analysis": ai_response["response"],
        "insights": ["Automated insights based on AI analysis"],
        "recommendations": ["Review the analysis and validate with actual data"],
        "confidence": ai_response["confidence"]
    }

async def research_task(task: Dict) -> Dict:
    """Research task"""
    prompt = f"""
    Conduct comprehensive research on:
    
    {task['description']}
    
    Provide:
    - Key findings
    - Multiple perspectives
    - Reliable sources (note: this is simulated)
    - Summary and conclusions
    """
    
    ai_response = await process_with_gemini(prompt, AssistantPersonality.PROFESSIONAL)
    
    return {
        "research": ai_response["response"],
        "sources": ["Note: In production, integrate with real research databases"],
        "summary": "Research completed using AI analysis",
        "confidence": ai_response["confidence"]
    }

async def general_ai_task(task: Dict) -> Dict:
    """General AI task processing"""
    ai_response = await process_with_gemini(task["description"], AssistantPersonality.JARVIS)
    
    return {
        "response": ai_response["response"],
        "confidence": ai_response["confidence"],
        "type": "general_assistance"
    }

@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """📊 Check AI task status and progress"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="🔍 Task not found")
    
    task = active_tasks[task_id]
    
    response = {
        "task_id": task_id,
        "type": task["type"],
        "status": task["status"],
        "progress": task["progress"],
        "created_at": task["created_at"]
    }
    
    if task["status"] == "completed":
        response["result"] = task["result"]
        response["completed_at"] = task["completed_at"]
    elif task["status"] == "failed":
        response["error"] = task["error"]
    
    return response

@app.get("/tasks/")
async def list_tasks(status: Optional[str] = Query(None), limit: int = Query(20, le=100)):
    """📋 List AI tasks with optional filtering"""
    tasks = list(active_tasks.values())
    
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    
    # Sort by priority and creation time
    tasks.sort(key=lambda t: (t["priority"], t["created_at"]), reverse=True)
    
    return {
        "total_tasks": len(active_tasks),
        "filtered_tasks": len(tasks),
        "tasks": tasks[:limit]
    }

# === AI AGENT ENDPOINTS ===

@app.post("/agents/analyze")
async def ai_agent_analysis(
    query: str = Form(..., description="What you want the AI agent to analyze or solve"),
    use_tools: bool = Form(True, description="Whether to use available tools")
):
    """
    🤖 Deploy AI Agent for Complex Problem Solving
    
    Let Jarvis use multiple AI tools and reasoning to solve complex problems autonomously.
    """
    if not llm:
        return {
            "query": query,
            "response": "AI agent analysis is available when LangChain is properly configured with API keys.",
            "tools_used": [],
            "confidence": 0.5
        }
    
    try:
        if use_tools:
            # Initialize agent with tools
            agent = initialize_agent(
                ai_tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            
            # Let the agent work
            result = agent.run(query)
            
            return {
                "query": query,
                "response": result,
                "tools_used": [tool.name for tool in ai_tools],
                "agent_type": "ReAct Agent with Tools",
                "confidence": 0.9
            }
        else:
            # Direct LLM response
            prompt_template = PromptTemplate(
                input_variables=["query"],
                template="Analyze and provide a comprehensive response to: {query}"
            )
            
            chain = LLMChain(llm=llm, prompt=prompt_template)
            result = chain.run(query=query)
            
            return {
                "query": query,
                "response": result,
                "tools_used": [],
                "agent_type": "Direct LLM",
                "confidence": 0.8
            }
            
    except Exception as e:
        return {
            "query": query,
            "response": f"Agent analysis failed: {str(e)}",
            "tools_used": [],
            "confidence": 0.3
        }

# === STREAMING AI RESPONSES ===

@app.get("/chat/stream/{conversation_id}")
async def stream_ai_response(
    conversation_id: str,
    message: str = Query(..., description="Message to send to AI")
):
    """
    🌊 Stream AI responses in real-time
    
    Get AI responses as they're generated for a more interactive experience.
    """
    async def generate_streaming_response():
        """Generate streaming AI response"""
        
        # Simulate streaming response
        response_parts = [
            "Let me think about that...",
            "Based on your question, I can see several important aspects to consider.",
            "First, let me analyze the key components of your request.",
            "Now, let me provide you with a comprehensive response:",
            "Here's my detailed analysis and recommendations for you."
        ]
        
        for i, part in enumerate(response_parts):
            yield f"data: {json.dumps({
                'type': 'thinking' if i == 0 else 'response',
                'content': part,
                'progress': (i + 1) / len(response_parts),
                'timestamp': datetime.now().isoformat()
            })}\n\n"
            
            await asyncio.sleep(1)  # Simulate processing time
        
        # Final complete response
        ai_response = await process_with_gemini(message, AssistantPersonality.JARVIS)
        
        yield f"data: {json.dumps({
            'type': 'complete',
            'content': ai_response['response'],
            'confidence': ai_response['confidence'],
            'progress': 1.0,
            'timestamp': datetime.now().isoformat()
        })}\n\n"
    
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/stream-stream",
        headers={"Cache-Control": "no-cache"}
    )

# === AI DEMO & EXAMPLES ===

@app.get("/demo/examples")
async def get_ai_examples():
    """🎯 Get example prompts and use cases for Jarvis AI"""
    return {
        "conversation_examples": [
            {
                "category": "General Chat",
                "examples": [
                    "Hello Jarvis, how are you today?",
                    "Can you help me plan my day?",
                    "What's the weather like?",
                    "Tell me a joke to brighten my mood"
                ]
            },
            {
                "category": "Problem Solving",
                "examples": [
                    "I need to optimize my daily routine",
                    "Help me brainstorm ideas for a startup",
                    "How can I improve my presentation skills?",
                    "What's the best approach to learn a new skill?"
                ]
            },
            {
                "category": "Technical Help",
                "examples": [
                    "Generate a Python function to calculate compound interest",
                    "Explain machine learning concepts in simple terms",
                    "Help me debug this code error",
                    "Design a database schema for an e-commerce app"
                ]
            }
        ],
        "document_qa_examples": [
            "What are the key points in this research paper?",
            "Summarize the main findings of this document",
            "What does this contract say about payment terms?",
            "Find all mentions of budget in this report"
        ],
        "task_automation_examples": [
            {
                "type": "code_generation",
                "description": "Create a REST API for user management with authentication"
            },
            {
                "type": "creative_writing", 
                "description": "Write a compelling product description for an AI assistant"
            },
            {
                "type": "data_analysis",
                "description": "Analyze customer feedback data and identify improvement opportunities"
            },
            {
                "type": "research",
                "description": "Research the latest trends in artificial intelligence and machine learning"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🤖 Starting Jarvis AI Personal Assistant Platform...")
    print("✨ Your intelligent companion is ready!")
    uvicorn.run(app, host="0.0.0.0", port=8000) 