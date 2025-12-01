from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.check import Check
from app.llmwrapper import GroqLLM
from app.firebase_config import check_firebase_connection, initialize_firebase
from app.redis_service import RedisChatService
from app.dependencies import get_current_user_id, get_optional_user_id

router = APIRouter()
checker = Check()

# Initialize services
try:
    llm = GroqLLM()
except Exception as e:
    print(f"Warning: Could not initialize GroqLLM - {e}")
    llm = None

try:
    initialize_firebase()
except Exception as e:
    print(f"Warning: Could not initialize Firebase - {e}")

# Initialize Redis service
redis_service = RedisChatService()


# System prompts for different user types
SYSTEM_PROMPT_PUBLIC = """You are a friendly customer service assistant for Laxmi Honey Industry, a premium honey company in Nepal. 

Company Information:
- We sell 100% pure, natural, and unprocessed honey
- We work directly with local beekeepers
- Free delivery on orders above Rs. 1000 across Nepal
- Standard delivery takes 2-3 business days
- Contact: +977 981-9492581, info@laxmibeekeeping.com.np
- CTO & MD: Biplov Gautam - cto@laxmibeekeeping.com.np
- We offer various types of honey products
- All products are of highest quality with no additives or preservatives

Provide helpful, friendly, and concise responses (2-3 sentences max). Use emojis appropriately. If the question is about products, delivery, contact info, or honey benefits, provide specific details from the company information above."""

SYSTEM_PROMPT_AUTHENTICATED = """You are a friendly customer service assistant for Laxmi Honey Industry, a premium honey company in Nepal.

Company Information:
- We sell 100% pure, natural, and unprocessed honey
- We work directly with local beekeepers
- Free delivery on orders above Rs. 1000 across Nepal
- Standard delivery takes 2-3 business days
- Contact: +977 981-9492581, info@laxmibeekeeping.com.np
- CTO & MD: Biplov Gautam - cto@laxmibeekeeping.com.np
- We offer various types of honey products
- All products are of highest quality with no additives or preservatives

As this is a registered user, you can provide more personalized assistance and detailed information about their orders, preferences, and account. Provide helpful, friendly, and concise responses (2-3 sentences max). Use emojis appropriately."""


class ChatRequest(BaseModel):
    message: str
    anonymousId: Optional[str] = Field(None, alias="anonymousId")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What honey products do you offer?",
                "anonymousId": "anon-12345"
            }
        }
        populate_by_name = True


class PromptRequest(BaseModel):
    prompt: str

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is FastAPI and why is it popular?"
            }
        }


@router.get("/health")
def health_check():
    return {"status": checker.checking(), "service": "laxmihoney"}


@router.get("/firebase-check")
def firebase_check():
    """
    Check Firebase connection status and configuration.
    Returns detailed information about Firebase initialization.
    """
    result = check_firebase_connection()
    
    if result["status"] == "connected":
        return {
            "status": "success",
            "message": "Firebase is connected and operational",
            "details": result
        }
    elif result["status"] == "disconnected":
        return {
            "status": "warning",
            "message": result["message"],
            "details": result,
            "hint": "Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON in .env file"
        }
    else:
        return {
            "status": "error",
            "message": result["message"],
            "details": result
        }


@router.post("/llm/public")
def public_chat(request: ChatRequest):
    """
    Public chatbot endpoint for non-logged-in users with multi-turn conversation support.
    Uses anonymous session ID for temporary conversation history (24 hours).
    
    Requires:
        - Message in request body
        - anonymousId in request body for session tracking
    """
    if llm is None:
        raise HTTPException(
            status_code=500,
            detail="LLM not initialized. Check GROQ_LLM_API in .env file",
        )

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Check for anonymous ID
    if not request.anonymousId:
        raise HTTPException(
            status_code=400,
            detail="Anonymous ID is required for public chat session."
        )

    try:
        # Generate temporary Redis key for anonymous user
        redis_key = f"chat-anon:{request.anonymousId}:main"
        
        # Generate full prompt with chat history
        full_prompt = redis_service.generate_full_prompt(
            redis_key,
            request.message,
            SYSTEM_PROMPT_PUBLIC
        )
        
        # Call LLM with full context
        response = llm._call(full_prompt)
        
        # Save to chat history (expires in 24 hours)
        redis_service.save_chat_history(redis_key, request.message, response)
        
        return {
            "message": request.message,
            "response": response,
            "user_type": "public",
            "anonymous_id": request.anonymousId,
            "model": llm.model,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post("/llm/authenticated")
def authenticated_chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Authenticated chatbot endpoint for logged-in users with multi-turn conversation support.
    Uses Firebase Auth for secure user identification and Redis for session memory.
    
    Requires:
        - Valid Firebase ID token in Authorization header
        - Message in request body
    """
    if llm is None:
        raise HTTPException(
            status_code=500,
            detail="LLM not initialized. Check GROQ_LLM_API in .env file",
        )

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Generate secure Redis key for authenticated user
        redis_key = f"chat-auth:{user_id}:main"
        
        # Generate full prompt with chat history
        full_prompt = redis_service.generate_full_prompt(
            redis_key,
            request.message,
            SYSTEM_PROMPT_AUTHENTICATED
        )
        
        # Call LLM with full context
        response = llm._call(full_prompt)
        
        # Save to chat history
        redis_service.save_chat_history(redis_key, request.message, response)
        
        return {
            "message": request.message,
            "response": response,
            "user_type": "authenticated",
            "user_id": user_id,
            "model": llm.model,
            "status": "success",
        }
    except HTTPException:
        # Re-raise HTTP exceptions (auth failures)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post("/llm")
def test_llm(request: PromptRequest):
    """
    Legacy LLM endpoint for backward compatibility and testing.
    This endpoint accepts raw prompts without system context.
    """
    if llm is None:
        raise HTTPException(
            status_code=500,
            detail="LLM not initialized. Check GROQ_LLM_API in .env file",
        )

    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    try:
        response = llm._call(request.prompt)
        return {
            "prompt": request.prompt,
            "response": response,
            "model": llm.model,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.get("/llm/history")
def get_chat_history(
    token_cred: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    anon_id: Optional[str] = Query(None, alias="anonymousId")
):
    """
    Get chat history for authenticated or anonymous users.
    
    For authenticated users: Provide Bearer token in Authorization header
    For anonymous users: Provide anonymousId as query parameter
    
    Returns:
        Chat history as a list of message objects with 'role' and 'content'
    """
    redis_key = None
    user_type = None
    
    # Debug logging
    print(f"🔍 /llm/history called:")
    print(f"   - Has Authorization header: {token_cred is not None and token_cred.credentials is not None}")
    print(f"   - Has anonymousId: {anon_id is not None}")
    if token_cred and token_cred.credentials:
        print(f"   - Token preview: {token_cred.credentials[:20]}...")
    
    # Check for authenticated user first
    if token_cred and token_cred.credentials:
        try:
            from app.firebase_config import verify_firebase_token
            print(f"   - Attempting Firebase token verification...")
            decoded_token = verify_firebase_token(token_cred.credentials)
            
            if decoded_token and "uid" in decoded_token:
                user_id = decoded_token["uid"]
                redis_key = f"chat-auth:{user_id}:main"
                user_type = "authenticated"
                print(f"   ✅ Token verified! User ID: {user_id}")
            else:
                print(f"   ❌ Token verification returned invalid data: {decoded_token}")
        except Exception as e:
            print(f"   ❌ Token verification failed: {e}")
    
    # If not authenticated, check for anonymous ID
    if not redis_key and anon_id:
        redis_key = f"chat-anon:{anon_id}:main"
        user_type = "anonymous"
        print(f"   ℹ️ Using anonymous session: {anon_id}")
    
    # If neither authenticated nor anonymous
    if not redis_key:
        raise HTTPException(
            status_code=400,
            detail="Either provide authentication token or anonymousId query parameter"
        )
    
    try:
        history = redis_service.get_history(redis_key)
        return {
            "history": history,
            "user_type": user_type,
            "message_count": len(history),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving chat history: {str(e)}"
        )


@router.delete("/llm/clearchat")
def clear_chat_history(user_id: str = Depends(get_current_user_id)):
    """
    Clear chat history for authenticated user.
    Requires valid Firebase authentication token.
    
    Returns:
        Status message indicating success or failure
    """
    try:
        # Construct authenticated Redis key
        redis_key = f"chat-auth:{user_id}:main"
        
        # Delete the chat history
        deleted_count = redis_service.delete_key(redis_key)
        
        if deleted_count > 0:
            return {
                "status": "success",
                "message": "Chat history cleared successfully",
                "user_id": user_id
            }
        else:
            return {
                "status": "success",
                "message": "No chat history found to clear",
                "user_id": user_id
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing chat history: {str(e)}"
        )


@router.get("/auth/verify")
def verify_token(user_id: str = Depends(get_current_user_id)):
    """
    Debug endpoint to verify Firebase authentication token.
    Use this to test if your token is valid.
    
    Returns:
        User ID and token validation status
    """
    return {
        "status": "success",
        "message": "Token is valid",
        "user_id": user_id,
        "authenticated": True
    }

