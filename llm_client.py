
# ============================================================================
# llm_client.py - Enhanced LLM Client with Better Error Handling
# ============================================================================

import requests
import logging
import time
import json
from typing import Dict, Any, Optional, Union
from config import MODEL_HOST, MODEL_OPEN_AI_KEY, DEFAULT_MODEL

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, host: str = MODEL_HOST, api_key: str = MODEL_OPEN_AI_KEY, default_model: str = DEFAULT_MODEL):
        self.host = host
        self.api_key = api_key
        self.default_model = default_model
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })

    def generate_response(self, prompt: str, model: Optional[str] = None, 
                         max_tokens: int = 2000, temperature: float = 0.3,
                         return_json: bool = True) -> Union[str, Dict[str, Any]]:
        """Generate response with enhanced error handling and retries"""
        
        model = model or self.default_model
        start_time = time.time()
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
            "top_p": 0.9,
            "top_k": 40
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"LLM request attempt {attempt + 1}/{max_retries}")
                
                response = self.session.post(
                    f"{self.host}/v1/chat/completions",
                    json=payload,
                    timeout=180
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                if "choices" not in response_data or not response_data["choices"]:
                    raise ValueError("Invalid response format from LLM")
                
                content = response_data["choices"][0]["message"]["content"]
                
                request_time = time.time() - start_time
                logger.info(f"LLM request completed in {request_time:.2f}s")
                
                if return_json:
                    return response_data
                return content.strip()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise Exception("LLM request timed out after all retries")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"LLM request failed: {e}")
                time.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"LLM generation failed: {e}")
                time.sleep(2 ** attempt)

    def test_connection(self) -> bool:
        """Test LLM connectivity"""
        try:
            response = self.generate_response(
                "Test connection. Respond with 'OK'.", 
                max_tokens=10, 
                return_json=False
            )
            logger.info("LLM connection test successful")
            return True
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
