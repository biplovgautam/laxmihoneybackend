from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.check import Check
from app.llmwrapper import GroqLLM
import os

app = FastAPI()

# Configure CORS - allows frontend to access the API
origins = [
    "http://localhost:3000",          # Local development
    "https://laxmibeekeeping.com.np", # Production frontend
    "https://www.laxmibeekeeping.com.np", # Production frontend with www
]

# If you have a specific frontend URL in environment variable
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins or ["*"] for all (not recommended for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def main():
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check():
    checker = Check()
    return {"status": checker.checking()}

# Initialize GroqLLM once at startup
try:
    llm = GroqLLM()
except Exception as e:
    print(f"Warning: Could not initialize GroqLLM - {e}")
    llm = None

# Request model for LLM endpoint
class PromptRequest(BaseModel):
    prompt: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is FastAPI and why is it popular?"
            }
        }


@app.post("/llm")
def test_llm(request: PromptRequest):
    """
    Test the GroqLLM functionality by sending a prompt and receiving a response.
    
    - **prompt**: Your question or prompt for the LLM
    """
    if llm is None:
        raise HTTPException(
            status_code=500, 
            detail="LLM not initialized. Check GROQ_LLM_API in .env file"
        )
    
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(
            status_code=400, 
            detail="Prompt cannot be empty"
        )
    
    try:
        response = llm._call(request.prompt)
        return {
            "prompt": request.prompt,
            "response": response,
            "model": llm.model,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating response: {str(e)}"
        )