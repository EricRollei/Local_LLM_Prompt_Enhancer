"""
LLM Backend handlers for LM Studio and Ollama
Handles API communication with local LLM servers
"""

import requests
import json
from typing import Dict, Optional, List


class LLMBackend:
    """Handles communication with local LLM backends"""
    
    def __init__(self, backend_type: str, endpoint: str, model_name: str, temperature: float = 0.7):
        self.backend_type = backend_type.lower()
        self.endpoint = endpoint.rstrip('/')
        self.model_name = model_name
        self.temperature = temperature
        
    def send_prompt(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Dict:
        """
        Send prompt to LLM and get response
        
        Args:
            system_prompt: System instructions
            user_prompt: User's prompt to expand
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with 'success', 'response', and 'error' keys
        """
        try:
            if self.backend_type == "lm_studio":
                return self._call_lm_studio(system_prompt, user_prompt, max_tokens)
            elif self.backend_type == "ollama":
                return self._call_ollama(system_prompt, user_prompt, max_tokens)
            else:
                return {
                    "success": False,
                    "response": "",
                    "error": f"Unknown backend type: {self.backend_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"LLM Backend Error: {str(e)}"
            }
    
    def _call_lm_studio(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Dict:
        """Call LM Studio API (OpenAI-compatible)"""
        url = f"{self.endpoint}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Request timed out. LLM took too long to respond."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to LM Studio at {self.endpoint}. Is it running?"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"LM Studio Error: {str(e)}"
            }
    
    def _call_ollama(self, system_prompt: str, user_prompt: str, max_tokens: int) -> Dict:
        """Call Ollama API"""
        url = f"{self.endpoint}/api/generate"
        
        # Combine system and user prompts for Ollama
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            data = response.json()
            content = data.get('response', '')
            
            return {
                "success": True,
                "response": content.strip(),
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "response": "",
                "error": "Request timed out. LLM took too long to respond."
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "response": "",
                "error": f"Cannot connect to Ollama at {self.endpoint}. Is it running?"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "error": f"Ollama Error: {str(e)}"
            }
    
    def test_connection(self) -> Dict:
        """Test if LLM backend is accessible"""
        try:
            if self.backend_type == "lm_studio":
                url = f"{self.endpoint}/models"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return {"success": True, "message": "LM Studio connected"}
            elif self.backend_type == "ollama":
                url = f"{self.endpoint}/api/tags"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return {"success": True, "message": "Ollama connected"}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}
