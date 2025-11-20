from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.check import Check
from app.llmwrapper import GroqLLM

router = APIRouter()
checker = Check()

try:
    llm = GroqLLM()
except Exception as e:
    print(f"Warning: Could not initialize GroqLLM - {e}")
    llm = None


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


@router.post("/llm")
def test_llm(request: PromptRequest):
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
