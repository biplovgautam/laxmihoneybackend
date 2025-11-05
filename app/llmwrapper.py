"""
GroqLLM Wrapper for LangChain
Automatically loads API key from environment variables
"""

import os
import requests
from typing import Optional, List, Any, Mapping
from langchain_core.language_models.llms import LLM
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GroqLLM(LLM):
    """
    Custom LangChain wrapper for Groq's chat API
    Automatically loads GROQ_LLM_API from environment variables
    
    Usage:
        llm = GroqLLM()  # API key loaded automatically
        response = llm("What is the capital of France?")
    """
    
    api_key: Optional[str] = None
    model: str = "llama-3.1-8b-instant"
    temperature: float = 0.7
    max_tokens: int = 1024
    
    def __init__(self, **kwargs):
        """Initialize with automatic API key loading"""
        super().__init__(**kwargs)
        
        # Load API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv('GROQ_LLM_API')
            
        if not self.api_key:
            raise ValueError(
                "GROQ_LLM_API not found in environment variables. "
                "Please add it to your .env file."
            )
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM"""
        return "groq"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """
        Call Groq API with error handling
        
        Args:
            prompt: The input prompt/question
            stop: Optional list of stop sequences
            
        Returns:
            Generated text response
        """
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "messages": [{"role": "user", "content": prompt}],
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            # Add stop sequences if provided
            if stop:
                data["stop"] = stop
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"Error: Network error calling Groq API - {str(e)}"
        except KeyError as e:
            return f"Error: Unexpected response format from Groq API - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    @property
    def _identifying_params(self):
        """Return identifying parameters for caching/logging"""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


# Convenience function for quick usage
def create_groq_llm(
    model: str = "llama-3.1-8b-instant",
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> GroqLLM:
    """
    Create a GroqLLM instance with custom parameters
    
    Args:
        model: Groq model name (default: llama-3.1-8b-instant)
        temperature: Sampling temperature 0-1 (default: 0.7)
        max_tokens: Maximum tokens in response (default: 1024)
        
    Returns:
        Configured GroqLLM instance
        
    Example:
        llm = create_groq_llm(temperature=0.5, max_tokens=512)
        response = llm("Explain quantum computing in simple terms")
    """
    return GroqLLM(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )