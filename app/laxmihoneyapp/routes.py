from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.check import Check
from app.llmwrapper import GroqLLM
from app.firebase_config import check_firebase_connection, initialize_firebase

router = APIRouter()
checker = Check()

try:
    llm = GroqLLM()
except Exception as e:
    print(f"Warning: Could not initialize GroqLLM - {e}")
    llm = None

# Initialize Firebase on module load
try:
    initialize_firebase()
except Exception as e:
    print(f"Warning: Could not initialize Firebase - {e}")


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

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What honey products do you offer?"
            }
        }


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
    Public chatbot endpoint for non-logged-in users.
    Uses the public system prompt with basic company information.
    """
    if llm is None:
        raise HTTPException(
            status_code=500,
            detail="LLM not initialized. Check GROQ_LLM_API in .env file",
        )

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = llm._call(request.message, system_prompt=SYSTEM_PROMPT_PUBLIC)
        return {
            "message": request.message,
            "response": response,
            "user_type": "public",
            "model": llm.model,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@router.post("/llm/authenticated")
def authenticated_chat(request: ChatRequest):
    """
    Authenticated chatbot endpoint for logged-in users.
    Uses the authenticated system prompt with personalized assistance capabilities.
    
    Note: In a production environment, this should include proper authentication
    middleware (e.g., JWT token verification) to validate the user's identity.
    """
    if llm is None:
        raise HTTPException(
            status_code=500,
            detail="LLM not initialized. Check GROQ_LLM_API in .env file",
        )

    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        response = llm._call(request.message, system_prompt=SYSTEM_PROMPT_AUTHENTICATED)
        return {
            "message": request.message,
            "response": response,
            "user_type": "authenticated",
            "model": llm.model,
            "status": "success",
        }
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
