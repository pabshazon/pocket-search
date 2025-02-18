import requests
import logging
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.model_name = None
        self.config = {}
        self.device = torch.device('cpu')  # Dummy device for compatibility
        
    @classmethod
    def from_pretrained(cls, 
                       model_name: str, 
                       config: Optional[Any] = None,
                       **kwargs) -> 'OllamaService':
        if model_name.startswith("ollama://"):
            model_name = model_name[len("ollama://"):]
        
        instance = cls()
        instance.model_name = model_name
        instance.config = kwargs
        return instance

    def to(self, device: torch.device) -> 'OllamaService':
        """Mock implementation of to() for device compatibility"""
        self.device = device
        return self
        
    def generate(self, 
                 prompt: str,
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 **kwargs) -> str:
        """
        Generate a response using an Ollama model.
        Returns the response text directly instead of JSON for compatibility.
        """
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False,
                **self.config,
                **kwargs
            }
            
            if system:
                payload["system"] = system
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            response_json = response.json()
            return response_json.get('response', '')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing Ollama response: {str(e)}")
            raise
