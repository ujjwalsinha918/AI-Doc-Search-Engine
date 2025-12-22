from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
from backend.api.helpers import summarize, search, extract

# Local utilities & RAG pipeline
from backend.utils.utils import get_current_user
from backend.rag.pipeline import get_or_create_collection
# @tool → tells LLM “this function can be called”
from langchain_core.tools import tool 
# ChatOllama → supports tool calling
from langchain_ollama import ChatOllama
# HumanMessage → user input
# ToolMessage → tool result sent back to LLM
from langchain_core.messages import HumanMessage, ToolMessage
# partial → pre-fill user_email automatically
from functools import partial

# Local LLM - THIS IS REQUIRED
from langchain_ollama import OllamaLLM

# Initialize the local LLM
llm = ChatOllama(
    model="llama3.2:3b",
    temperature=0.3,
)

router = APIRouter(prefix="/api", tags=["chat"])

@tool
def rag_search(query: str, document_id: int | None = None, user_email: str | None = None) -> str:
    """Search the user's documents for relevant information."""
    if not user_email:
        return "Error: User not authenticated."
    docs, _ = search(query=query, document_id=document_id, user_email=user_email)
    if not docs:
        return "No relevant information found."
    return "\n\n".join(docs[:10])

@tool
def rag_summarize(document_id: int | None = None, user_email: str | None = None) -> str:
    """Generate a concise summary of the user's documents."""
    if not user_email:
        return "Error: User not authenticated."
    docs, _ = search(query="", document_id=document_id, user_email=user_email)
    return summarize(docs)

@tool
def rag_extract(field: str, document_id: int | None = None, user_email: str | None = None) -> str:
    """Extract specific information like names, emails, dates from documents."""
    if not user_email:
        return "Error: User not authenticated."
    docs, _ = search(query=field, document_id=document_id, user_email=user_email)
    results = extract(docs, field)
    if not results:
        return f"No '{field}' found in documents."
    return "\n".join(results[:20])

# ----------------------
# Request schema
# ----------------------
class ChatRequest(BaseModel):
    message: str
    document_id: int | None = None  # list of filenames to query 

# ----------------------
# Chat endpoint
# ----------------------
@router.post("/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    
    user_email = current_user["email"]
    
    if not request.message or not request.message.strip():
        return StreamingResponse(
            iter(["data: [DONE]\n\n"]),
            media_type="text/event-stream"
        )
    
    # Bind tools with user_email pre-filled    
    # tools = [
    #     partial(rag_search, user_email=user_email),
    #     partial(rag_summarize, user_email=user_email),
    #     partial(rag_extract, user_email=user_email),
    # ]    
    
    # LLM decides when to call tools
    model_with_tools = llm.bind_tools([
    rag_search,
    rag_summarize,
    rag_extract,
])
    
    # Tool-calling streaming loop
    messages = [HumanMessage(content=request.message)]
        
#     # Identify user (used to isolate their documents)
#     user_email = current_user["email"]
    
#     # call helpers here
#     docs, metas = search(
#         query=request.message,
#         document_id= request.document_id,
#         user_email=user_email
#     )
    
#     # default to empty list if None
#     docs = docs or []
#     metas = metas or []    
       
#     # 5. Build context and citation list
#     context_parts = []    # Holds retrieved document text
#     sources = []          # Holds citation 
    
#     # Build context and citation list
#     if docs and metas:
#         for i, (doc, meta) in enumerate(zip(docs, metas)):
#             context_parts.append(f"[{i+1}] {doc}")
#             sources.append({"document_id": meta.get("document_id"), "source": meta.get("filename","unknown"), "page": meta.get("page", "?")})

#         context = "\n\n".join(context_parts) if context_parts else "No Relevant Documents found."

#     # Prompt for LLM
#     prompt = f"""You are a helpful AI assistant. Answer using ONLY this context:

# {context}

# Question: {request.message}

# Rules:
# - If question is vague, ask for clarification
# - If no relevant info exists, say so clearly


# Answer naturally. Cite sources with [1], [2] if used.
# If no info, say: "I don't have information about that in your documents."
# """

    # Streaming generator for LLM output to frontend
    def stream_response():
        try:
            # First pass: stream initial response + detect tool calls
            tool_call_results = {}

            for chunk in model_with_tools.stream(messages):
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

                # Collect tool calls
                if chunk.tool_calls:   # Detect tool calls
                    for tool_call in chunk.tool_calls:
                        tool_name = tool_call["name"]
                        args = tool_call["args"]
                        tool_id = tool_call["id"]

                        # Execute tool
                        # Parse LLM intent
                        if tool_name == "rag_search":
                            result = rag_search.invoke({**args, "user_email": user_email})
                        elif tool_name == "rag_summarize":
                            result = rag_summarize.invoke({**args, "user_email": user_email})
                            
                        elif tool_name == "rag_extract":
                            result = rag_extract.invoke({**args, "user_email": user_email})
                            # ->calls search(...)
                        # → retrieves chunks from Chroma
                        # → runs extract(...)
                        # → returns matching text
                        else:
                            result = "Unknown tool."

                        tool_call_results[tool_id] = result

                        # Add to messages for final answer
                        messages.append(chunk)
                        # Send result back to LLM, Read tool output
                        messages.append(ToolMessage(content=result, tool_call_id=tool_id))
                        # now llm has user question, retrieved knowledge and tool results

            # After tool calls, get final answer
            if tool_call_results:
                # LLM formats, explains, and reasons over tool output
                final_response = llm.invoke(messages)
                for token in final_response.content:
                    if isinstance(token, str):
                        yield f"data: {json.dumps({'content': token})}\n\n"
                    elif hasattr(token, 'content'):
                        yield f"data: {json.dumps({'content': token.content})}\n\n"

            # Always send citations (you can enhance this later)
            yield f"data: {json.dumps({'citations': []})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")
