# Option 1: Simple HTTP requests test
import requests
import json

def test_llm_endpoint_simple():
    """Basic connectivity test"""
    llm_url = "{MODEL_HOST}/api/chat"  # Replace with your LLM endpoint
    
    test_payload = {
        "prompt": "Hello, are you working?",
        "max_tokens": 50
    }
    
    try:
        response = requests.post(llm_url, json=test_payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ LLM endpoint is responding")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ LLM endpoint returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LLM endpoint - is it running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ LLM endpoint timeout - taking too long to respond")
        return False
    except Exception as e:
        print(f"❌ Error testing LLM endpoint: {str(e)}")
        return False

# Option 2: More comprehensive test with question generation
def test_llm_question_generation():
    """Test actual question generation functionality"""
    llm_url = "{MODEL_HOST}/api/chat"  # Replace with your LLM endpoint
    
    test_prompt = """
    Generate a multiple choice question about photosynthesis with 4 options.
    Return only JSON format with: question, options array, correct_answer_index, explanation
    """
    
    payload = {
        "prompt": test_prompt,
        "max_tokens": 300,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(llm_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ LLM can generate questions")
            print(f"Generated content: {result}")
            
            # Optional: Try to parse if it returns valid JSON
            try:
                if 'response' in result:
                    generated_json = json.loads(result['response'])
                    print("✅ LLM returned valid JSON structure")
                elif 'choices' in result and len(result['choices']) > 0:
                    generated_text = result['choices'][0]['text']
                    generated_json = json.loads(generated_text)
                    print("✅ LLM returned valid JSON structure")
            except json.JSONDecodeError:
                print("⚠️ LLM response is not valid JSON - may need prompt engineering")
            
            return True
        else:
            print(f"❌ LLM endpoint error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing question generation: {str(e)}")
        return False

# Option 3: Health check endpoint (if your LLM has one)
def test_llm_health():
    """Test LLM health endpoint if available"""
    health_url = "{MODEL_HOST}/health"  # Common health check endpoint
    
    try:
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print("✅ LLM health check passed")
            return True
        else:
            print(f"❌ LLM health check failed: {response.status_code}")
            return False
    except:
        print("⚠️ No health endpoint available")
        return None

# Option 4: Integration into your API endpoint
def test_in_api_endpoint():
    """Example of how to test within your API code"""
    
    def check_llm_connection():
        """Add this function to your API code"""
        try:
            # Simple ping test
            test_response = requests.post(
                "{MODEL_HOST}/api/chat",
                json={"prompt": "ping", "max_tokens": 10},
                timeout=5
            )
            return test_response.status_code == 200
        except:
            return False
    
    # Use in your API endpoint
    if not check_llm_connection():
        return {
            "success": False,
            "error": "LLM service is currently unavailable"
        }, 503
    
    # Continue with normal processing...
    return {"success": True}

# Option 5: Quick curl command test (run in terminal)
def generate_curl_test():
    """Generates curl command for manual testing"""
    curl_command = '''
# Test basic connectivity
curl -X POST {MODEL_HOST}/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, are you working?", "max_tokens": 50}'

# Test question generation
curl -X POST {MODEL_HOST}/api/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Generate a simple math question with answer", "max_tokens": 100}'
'''
    print("Run these curl commands in your terminal:")
    print(curl_command)

# Run all tests
if __name__ == "__main__":
    print("Testing LLM Endpoint...")
    print("=" * 50)
    
    # Run tests in order
    test_llm_health()
    test_llm_endpoint_simple()
    test_llm_question_generation()
    
    print("\n" + "=" * 50)
    print("Manual curl test commands:")
    generate_curl_test()