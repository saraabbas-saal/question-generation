import requests
import logging
import time
import json
from typing import Dict, Any, Optional
from config import MODEL_HOST, MODEL_OPEN_AI_KEY, DEFAULT_MODEL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_llm_response(prompt: str, model: Optional[str] = None, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """
    Get response from LLM service with detailed logging
    
    Args:
        prompt (str): The input prompt for the LLM
        model (str, optional): Model name to use, defaults to DEFAULT_MODEL
        max_tokens (int): Maximum tokens in response
        temperature (float): Temperature for response generation
        
    Returns:
        str: Generated response from LLM
        
    Raises:
        Exception: If LLM service call fails
    """
    
    logger.info("Starting LLM request...")
    start_time = time.time()
    
    if model is None:
        model = DEFAULT_MODEL
        logger.debug(f"Using default model: {model}")
    else:
        logger.debug(f"Using specified model: {model}")
    
    # Prepare the request payload
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MODEL_OPEN_AI_KEY}"
    }
    
   
    try:
        logger.info(f"Sending request to: {MODEL_HOST}/v1/chat/completions")
        
        # Make the API call
        response = requests.post(
            f"{MODEL_HOST}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=120  # 2 minute timeout
        )
        
        request_time = time.time() - start_time
        logger.info(f"⏱️  Request completed in {request_time:.2f} seconds")
        
        # Log response details
        logger.info(f"📥 Response Details:")
        logger.info(f"   📊 Status Code: {response.status_code}")
        logger.info(f"   📏 Response Size: {len(response.content)} bytes")
        logger.debug(f"   📋 Response Headers: {dict(response.headers)}")
        
        # Check if request was successful
        response.raise_for_status()
        logger.info("✅ HTTP request successful")
        
        # Parse the response
        try:
            response_data = response.json()
            logger.debug(f"📄 Raw response data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON response: {e}")
            logger.error(f"Raw response text: {response.text}")
            raise Exception("Invalid JSON response from LLM service")
        
        # Extract the generated text
        if "choices" in response_data and len(response_data["choices"]) > 0:
            generated_text = response_data["choices"][0]["message"]["content"]
            logger.info(f"✅ Successfully received LLM response")
            logger.info(f"   📝 Generated text length: {len(generated_text)} characters")
            logger.debug(f"   📄 Generated text preview: {generated_text[:200]}...")
            
            total_time = time.time() - start_time
            logger.info(f"🎉 LLM request completed successfully in {total_time:.2f} seconds")
            
            return generated_text.strip()
        else:
            logger.error("❌ Invalid response format from LLM service")
            logger.error(f"Response data structure: {response_data}")
            raise Exception("Invalid response format from LLM service")
            
    except requests.exceptions.Timeout:
        request_time = time.time() - start_time
        logger.error(f"⏰ LLM service request timed out after {request_time:.2f} seconds")
        logger.error(f"   🔗 Target: {MODEL_HOST}/v1/chat/completions")
        logger.error(f"   ⏱️  Timeout limit: 120 seconds")
        raise Exception("LLM service request timed out")
        
    except requests.exceptions.ConnectionError as e:
        request_time = time.time() - start_time
        logger.error(f"🔌 Connection error after {request_time:.2f} seconds")
        logger.error(f"   🔗 Target: {MODEL_HOST}")
        logger.error(f"   ❌ Error: {e}")
        logger.error("   💡 Suggestions:")
        logger.error("      - Check if LLM service is running")
        logger.error("      - Verify network connectivity")
        logger.error("      - Check firewall settings")
        raise Exception(f"Could not connect to LLM service at {MODEL_HOST}")
        
    except requests.exceptions.HTTPError as e:
        request_time = time.time() - start_time
        logger.error(f"🚫 HTTP error after {request_time:.2f} seconds: {e}")
        logger.error(f"   📊 Status Code: {response.status_code}")
        logger.error(f"   📄 Response Text: {response.text}")
        raise Exception(f"LLM service returned HTTP error: {e}")
        
    except Exception as e:
        request_time = time.time() - start_time
        logger.error(f"💥 Unexpected error after {request_time:.2f} seconds: {e}")
        logger.error(f"   🔗 Target: {MODEL_HOST}")
        logger.error(f"   🤖 Model: {model}")
        raise Exception(f"LLM service call failed: {e}")

def get_llm_response_openai_format(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Get response from LLM service in OpenAI format (for compatibility)
    
    Args:
        prompt (str): The input prompt for the LLM
        model (str, optional): Model name to use
        
    Returns:
        Dict[str, Any]: Full response in OpenAI format
    """
    
    logger.info("📋 Getting LLM response in OpenAI format...")
    
    if model is None:
        model = DEFAULT_MODEL
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MODEL_OPEN_AI_KEY}"
    }
    
    logger.debug(f"OpenAI format request payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{MODEL_HOST}/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        logger.info("✅ OpenAI format response received successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in OpenAI format LLM call: {e}")
        raise Exception(f"LLM service call failed: {e}")

def validate_llm_connection() -> bool:
    """
    Test connection to LLM service with detailed logging
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    logger.info("🔍 Testing LLM connection...")
    
    try:
        test_prompt = "Hello, this is a connection test. Please respond with 'Connection successful.'"
        logger.info("📤 Sending test prompt to LLM...")
        
        response = get_llm_response(test_prompt, max_tokens=50)
        
        logger.info("✅ LLM connection test successful!")
        logger.info(f"   📝 Test response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM connection test failed: {e}")
        logger.error("   💡 Troubleshooting steps:")
        logger.error("      1. Check if LLM service is running")
        logger.error("      2. Verify the MODEL_HOST configuration")
        logger.error("      3. Test network connectivity")
        logger.error("      4. Check API key validity")
        return False

def test_llm_service_health():
    """
    Comprehensive health check of the LLM service
    """
    logger.info("🏥 Starting comprehensive LLM service health check...")
    
    # Test 1: Basic connectivity
    logger.info("🔌 Test 1: Basic connectivity")
    try:
        response = requests.get(MODEL_HOST, timeout=10)
        logger.info(f"✅ Basic connectivity successful - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Basic connectivity failed: {e}")
    
    # Test 2: Models endpoint
    logger.info("🤖 Test 2: Models endpoint")
    try:
        headers = {"Authorization": f"Bearer {MODEL_OPEN_AI_KEY}"}
        response = requests.get(f"{MODEL_HOST}/v1/models", headers=headers, timeout=30)
        logger.info(f"✅ Models endpoint accessible - Status: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            logger.info(f"   📋 Available models: {len(models.get('data', []))} models found")
    except Exception as e:
        logger.error(f"❌ Models endpoint failed: {e}")
    
    # Test 3: Simple completion
    logger.info("💬 Test 3: Simple completion test")
    try:
        result = validate_llm_connection()
        if result:
            logger.info("✅ Simple completion test passed")
        else:
            logger.error("❌ Simple completion test failed")
    except Exception as e:
        logger.error(f"❌ Simple completion test error: {e}")
    
    logger.info("🏁 Health check completed")

# Initialize logging
logger.info("🔧 LLM Utils module loaded successfully")
logger.info(f"   🔗 Target Host: {MODEL_HOST}")
logger.info(f"   🤖 Default Model: {DEFAULT_MODEL}")