"""
Redis Chat Service for Multi-Turn Conversations
Manages chat history storage and retrieval using Redis
"""

import os
import json
from typing import List, Dict, Optional
import redis
from dotenv import load_dotenv

load_dotenv()


class RedisChatService:
    """Service for managing chat history in Redis"""
    
    def __init__(self):
        """Initialize Redis connection"""
        # Check for individual Redis Cloud credentials first
        redis_host = os.getenv('REDIS_HOST')
        redis_port = os.getenv('REDIS_PORT')
        redis_username = os.getenv('REDIS_USERNAME', 'default')
        redis_password = os.getenv('REDIS_PASSWORD')
        
        # Fallback to REDIS_URL if available
        redis_url = os.getenv('REDIS_URL')
        
        try:
            # Use individual credentials if available (Redis Cloud)
            if redis_host and redis_port and redis_password:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=int(redis_port),
                    username=redis_username,
                    password=redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                print(f"✅ Connecting to Redis Cloud at {redis_host}:{redis_port}")
            
            # Fallback to URL-based connection
            elif redis_url:
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                print(f"✅ Connecting to Redis via URL")
            
            else:
                print("⚠️ No Redis configuration found. Set REDIS_HOST/PORT/PASSWORD or REDIS_URL in .env")
                self.redis_client = None
                return
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connected successfully")
            
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            self.redis_client = None
    
    def save_chat_history(self, key: str, user_message: str, bot_response: str) -> bool:
        """
        Save a user-bot message pair to Redis
        
        Args:
            key: Redis key for the chat session
            user_message: User's message
            bot_response: Bot's response
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            print("Redis not available, skipping history save")
            return False
        
        try:
            # Create message pair
            messages = [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": bot_response}
            ]
            
            # Append to Redis list
            for msg in messages:
                self.redis_client.rpush(key, json.dumps(msg))
            
            # Set expiration (24 hours for anonymous, 30 days for authenticated)
            if "chat-anon:" in key:
                self.redis_client.expire(key, 86400)  # 24 hours
            else:
                self.redis_client.expire(key, 2592000)  # 30 days
            
            return True
        except Exception as e:
            print(f"Error saving chat history: {e}")
            return False
    
    def get_history(self, key: str) -> List[Dict[str, str]]:
        """
        Retrieve chat history from Redis
        
        Args:
            key: Redis key for the chat session
            
        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        if not self.redis_client:
            return []
        
        try:
            # Get all messages from list
            messages_raw = self.redis_client.lrange(key, 0, -1)
            
            # Parse JSON messages
            messages = []
            for msg_str in messages_raw:
                try:
                    messages.append(json.loads(msg_str))
                except json.JSONDecodeError:
                    continue
            
            return messages
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []
    
    def delete_key(self, key: str) -> int:
        """
        Delete a chat session from Redis
        
        Args:
            key: Redis key to delete
            
        Returns:
            Number of keys deleted (0 or 1)
        """
        if not self.redis_client:
            return 0
        
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            print(f"Error deleting key: {e}")
            return 0
    
    def generate_full_prompt(
        self, 
        key: str, 
        new_message: str, 
        system_prompt: str,
        max_history: int = 10
    ) -> str:
        """
        Generate a full prompt including chat history, system prompt, and new message
        
        Args:
            key: Redis key for the chat session
            new_message: New user message
            system_prompt: System prompt for context
            max_history: Maximum number of previous messages to include
            
        Returns:
            Formatted prompt string for the LLM
        """
        # Get chat history
        history = self.get_history(key)
        
        # Limit history to recent messages (keep last N exchanges)
        if len(history) > max_history * 2:  # *2 because each exchange has 2 messages
            history = history[-(max_history * 2):]
        
        # Build the full prompt
        prompt_parts = []
        
        # Add system context if this is the first message
        if not history:
            prompt_parts.append(f"System Context: {system_prompt}")
            prompt_parts.append("\n---\n")
        
        # Add conversation history
        if history:
            prompt_parts.append("Previous conversation:\n")
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                prompt_parts.append(f"{role}: {msg['content']}\n")
            prompt_parts.append("\n---\n")
        
        # Add new message
        prompt_parts.append(f"User: {new_message}\n")
        prompt_parts.append("Assistant:")
        
        return "".join(prompt_parts)
    
    def check_connection(self) -> Dict[str, any]:
        """
        Check Redis connection status
        
        Returns:
            Dictionary with connection status information
        """
        if not self.redis_client:
            return {
                "status": "disconnected",
                "message": "Redis client not initialized"
            }
        
        try:
            self.redis_client.ping()
            info = self.redis_client.info()
            return {
                "status": "connected",
                "message": "Redis is operational",
                "version": info.get("redis_version"),
                "uptime_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Redis connection error: {str(e)}"
            }
