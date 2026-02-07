"""Groq API client for LLM generation"""
import os
import json
from typing import Optional, Dict, Any
from groq import Groq
from corep_assistant.config import GROQ_API_KEY, GROQ_MODEL_NAME


class RateLimitError(Exception):
    """Custom exception for Groq rate limits"""
    pass


class GroqClient:
    """Client for Groq API using official SDK"""
    
    def __init__(
        self,
        api_key: str = GROQ_API_KEY,
        model: str = GROQ_MODEL_NAME,
        timeout: float = 60.0,
        max_retries: int = 3
    ):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model: Model name
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize official Groq client
        self.client = Groq(api_key=self.api_key)
    
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Optional[Dict]:
        """
        Generate JSON response from Groq API.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON dict or None on failure
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        for attempt in range(self.max_retries):
            try:
                # Use official Groq SDK
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}  # Force JSON mode
                )
                
                # Extract content
                content = completion.choices[0].message.content
                
                # Parse JSON from content
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    print(f"Content: {content[:500]}")
                    return None
            
            except Exception as e:
                err_msg = str(e).lower()
                if "rate_limit_exceeded" in err_msg or "rate limit" in err_msg:
                    print(f"CRITICAL: Groq rate limit exceeded: {e}")
                    raise RateLimitError("Groq API rate limit reached. Please wait a minute before trying again.")
                
                print(f"Groq API error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    print(f"Retrying...")
                    continue
                return None
        
        return None


# Global instance
_groq_client = None


def get_groq_client() -> GroqClient:
    """Get global Groq client instance"""
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
