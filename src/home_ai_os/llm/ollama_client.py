"""Ollama client for local LLM inference."""

import subprocess
import time
import requests
from typing import Iterator, Optional, Dict, Any, List
from dataclasses import dataclass
from loguru import logger
import json

from home_ai_os.core.config import get_settings


@dataclass
class ModelInfo:
    """Information about an Ollama model."""
    name: str
    size: str
    modified: str
    available: bool = True


class OllamaClient:
    """
    Client for Ollama local LLM inference.
    Handles model management, streaming, and context.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url
        self.settings = get_settings()
        self.current_model = self.settings.llm.preferred_model
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info(f"OllamaClient initialized: {base_url}")
    
    def check_server(self) -> bool:
        """
        Check if Ollama server is running.
        
        Returns:
            True if server is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama server not accessible: {e}")
            return False
    
    def start_server(self) -> bool:
        """
        Start Ollama server if not running.
        
        Returns:
            True if server started successfully
        """
        if self.check_server():
            logger.info("Ollama server already running")
            return True
        
        try:
            logger.info("Starting Ollama server...")
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            for i in range(10):
                time.sleep(1)
                if self.check_server():
                    logger.info("Ollama server started successfully")
                    return True
            
            logger.error("Ollama server failed to start")
            return False
        
        except FileNotFoundError:
            logger.error("Ollama not installed. Please install from https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"Failed to start Ollama server: {e}")
            return False
    
    def list_models(self) -> List[ModelInfo]:
        """
        List available models.
        
        Returns:
            List of ModelInfo objects
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            data = response.json()
            models = []
            
            for model in data.get("models", []):
                models.append(ModelInfo(
                    name=model["name"],
                    size=model.get("size", "unknown"),
                    modified=model.get("modified_at", "unknown"),
                    available=True
                ))
            
            return models
        
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull (e.g., "mistral:7b")
        
        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {model_name}")
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get("status", "")
                    if status:
                        logger.debug(f"Pull status: {status}")
            
            logger.info(f"Model pulled successfully: {model_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    def ensure_model(self, model_name: Optional[str] = None) -> bool:
        """
        Ensure a model is available, pulling if necessary.
        
        Args:
            model_name: Model to ensure, or None for preferred model
        
        Returns:
            True if model is available
        """
        if model_name is None:
            model_name = self.current_model
        
        models = self.list_models()
        model_names = [m.name for m in models]
        
        if model_name in model_names:
            logger.info(f"Model available: {model_name}")
            return True
        
        logger.info(f"Model not found, attempting to pull: {model_name}")
        return self.pull_model(model_name)
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = True
    ) -> Iterator[str]:
        """
        Generate text from prompt with streaming.
        
        Args:
            prompt: User prompt
            model: Model to use (None for current model)
            system: System prompt
            temperature: Temperature (None for config default)
            stream: Whether to stream response
        
        Yields:
            Response chunks
        """
        if model is None:
            model = self.current_model
        
        if temperature is None:
            temperature = self.settings.llm.temperature
        
        request_data = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": self.settings.llm.top_p,
                "top_k": self.settings.llm.top_k,
            }
        }
        
        if system:
            request_data["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=request_data,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        if chunk:
                            yield chunk
                        
                        if data.get("done", False):
                            break
            else:
                data = response.json()
                yield data.get("response", "")
        
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            yield f"[Error: {str(e)}]"
    
    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = True,
        use_history: bool = True
    ) -> Iterator[str]:
        """
        Chat with the model using conversation history.
        
        Args:
            message: User message
            model: Model to use
            system: System prompt
            temperature: Temperature
            stream: Whether to stream
            use_history: Whether to use conversation history
        
        Yields:
            Response chunks
        """
        if model is None:
            model = self.current_model
        
        if temperature is None:
            temperature = self.settings.llm.temperature
        
        if use_history:
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
        
        messages = []
        if use_history:
            messages = self.conversation_history.copy()
        else:
            messages = [{"role": "user", "content": message}]
        
        request_data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": self.settings.llm.top_p,
                "top_k": self.settings.llm.top_k,
            }
        }
        
        if system:
            request_data["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=request_data,
                stream=stream
            )
            response.raise_for_status()
            
            full_response = ""
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_response += chunk
                            yield chunk
                        
                        if data.get("done", False):
                            break
            else:
                data = response.json()
                full_response = data.get("message", {}).get("content", "")
                yield full_response
            
            if use_history and full_response:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
        
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            yield f"[Error: {str(e)}]"
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def set_model(self, model_name: str) -> bool:
        """
        Set current model.
        
        Args:
            model_name: Model to use
        
        Returns:
            True if model is available
        """
        if self.ensure_model(model_name):
            self.current_model = model_name
            logger.info(f"Model set to: {model_name}")
            return True
        return False
    
    def detect_gpu(self) -> Dict[str, Any]:
        """
        Detect GPU availability.
        
        Returns:
            GPU information
        """
        gpu_info = {
            "available": False,
            "type": "none",
            "vram": 0
        }
        
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output:
                    parts = output.split(',')
                    gpu_info["available"] = True
                    gpu_info["type"] = "NVIDIA CUDA"
                    gpu_info["name"] = parts[0].strip()
                    if len(parts) > 1:
                        vram_str = parts[1].strip().split()[0]
                        gpu_info["vram"] = int(vram_str)
                    
                    logger.info(f"GPU detected: {gpu_info['name']} ({gpu_info['vram']} MB)")
                    return gpu_info
        
        except Exception:
            pass
        
        logger.info("No GPU detected, using CPU")
        gpu_info["type"] = "CPU"
        return gpu_info
    
    def select_optimal_model(self) -> str:
        """
        Select optimal model based on available hardware.
        
        Returns:
            Recommended model name
        """
        gpu_info = self.detect_gpu()
        
        if not gpu_info["available"]:
            logger.info("CPU mode: selecting phi3:mini")
            return "phi3:mini"
        
        vram_gb = gpu_info["vram"] / 1024
        
        if vram_gb >= 8:
            logger.info(f"High VRAM ({vram_gb:.1f}GB): selecting mistral:7b")
            return "mistral:7b-instruct"
        elif vram_gb >= 4:
            logger.info(f"Medium VRAM ({vram_gb:.1f}GB): selecting llama3.2:3b")
            return "llama3.2:3b"
        else:
            logger.info(f"Low VRAM ({vram_gb:.1f}GB): selecting phi3:mini")
            return "phi3:mini"


_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
