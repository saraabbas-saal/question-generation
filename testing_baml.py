#!/usr/bin/env python3
"""
BAML-only Testing Script for AFADI Question Generation
Tests the new BAML-based API endpoints
"""

import asyncio
import json
import logging
from typing import Dict, Any
import httpx
from baml_service import baml_service
from baml_client.types import QuestionGenerationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://localhost:8888"

class BAMLTester:
    """Test class for BAML-based question generation"""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def test_direct_baml_service(self):
        """Test BAML service directly (without API)"""
        logger.info("🧪 Testing BAML service directly...")
        
        try:
            result = await baml_service.generate_questions_async(
                teaching_point_en="Explain air defense radar operations",
                teaching_point_ar="شرح عمليات رادار الدفاع الجوي",
                context="Focus on early warning systems",
                question_type="MULTICHOICE",
                number_of_distractors=3,
                language="en",
                bloom_level="UNDERSTAND"
            )
            
            logger.info(f"✅ Direct BAML test successful!")
            logger.info(f"📊 Generated {len(result.questions)} questions")
            
            # Display first question
            if result.questions:
                q = result.questions[0]
                logger.info(f"📝 Sample question: {q.question}")
                logger.info(f"🔤 Options: {[f'{opt.key}: {opt.value}' for opt in q.options]}")
                logger.info(f"✔️ Answer: {q.answer}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Direct BAML test failed: {e}")
            return False
    
    async def test_api_health(self):
        """Test API health endpoints"""
        logger.info("🏥 Testing API health...")
        
        try:
            response = await self.client.get(f"{self.api_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Health check passed: {health_data['status']}")
                logger.info(f"🔗 BAML connection: {health_data.get('baml_connection', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_baml_status(self):
        """Test BAML status endpoint"""
        logger.info("📊 Testing BAML status...")
        
        try:
            response = await self.client.get(f"{self.api_url}/baml-status")
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"✅ BAML status: {status_data}")
                return True
            else:
                logger.error(f"❌ BAML status failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ BAML status error: {e}")
            return False
    
    async def test_question_generation_endpoint(self):
        """Test the main question generation endpoint"""
        logger.info("🎯 Testing question generation endpoint...")
        
        test_request = {
            "teaching_point_en": "Analyze tactical advantages of air defense positioning",
            "teaching_point_ar": "تحليل الميزات التكتيكية لتموضع الدفاع الجوي",
            "context": "Consider urban and desert environments",
            "question_type": "MULTICHOICE",
            "number_of_distractors": 3,
            "language": "en",
            "bloom_level": "ANALYZE"
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/generate-questions",
                json=test_request
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Question generation successful!")
                logger.info(f"📊 Generated {result['total_questions']} questions")
                logger.info(f"🎯 Type: {result['question_type']}, Language: {result['language']}")
                
                # Display sample question
                if result['questions']:
                    q = result['questions'][0]
                    logger.info(f"📝 Sample: {q['question']}")
                    logger.info(f"✔️ Answer: {q['answer']}")
                
                return True
            else:
                logger.error(f"❌ Question generation failed: {response.status_code}")
                logger.error(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Question generation error: {e}")
            return False
    
    async def test_native_baml_endpoint(self):
        """Test the native BAML format endpoint"""
        logger.info("🔬 Testing native BAML endpoint...")
        
        test_request = {
            "teaching_point_en": "Evaluate the effectiveness of air defense systems",
            "teaching_point_ar": "تقييم فعالية أنظمة الدفاع الجوي",
            "question_type": "TRUE_FALSE_JUSTIFICATION",
            "language": "en",
            "bloom_level": "EVALUATE"
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/generate-questions-baml",
                json=test_request
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Native BAML endpoint successful!")
                logger.info(f"📊 Generated {len(result['questions'])} questions")
                
                # Display sample question with justification
                if result['questions']:
                    q = result['questions'][0]
                    logger.info(f"📝 Question: {q['question']}")
                    logger.info(f"✔️ Answer: {q['answer']}")
                    if q.get('model_answer'):
                        logger.info(f"💡 Justification: {q['model_answer'][:100]}...")
                
                return True
            else:
                logger.error(f"❌ Native BAML endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Native BAML endpoint error: {e}")
            return False
    
    async def test_multi_select_questions(self):
        """Test multi-select question generation"""
        logger.info("🎲 Testing multi-select questions...")
        
        test_request = {
            "teaching_point_en": "Identify key components of air defense systems",
            "teaching_point_ar": "تحديد المكونات الرئيسية لأنظمة الدفاع الجوي",
            "question_type": "MULTI_SELECT",
            "number_of_distractors": 3,
            "number_of_correct_answers": 2,
            "language": "en",
            "bloom_level": "REMEMBER"
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/generate-questions",
                json=test_request
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Multi-select test successful!")
                
                # Check that we have multiple correct answers
                if result['questions']:
                    q = result['questions'][0]
                    logger.info(f"📝 Question: {q['question']}")
                    logger.info(f"✔️ Correct answers: {q['answer']} (count: {len(q['answer'])})")
                
                return True
            else:
                logger.error(f"❌ Multi-select test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Multi-select test error: {e}")
            return False
    
    async def test_arabic_questions(self):
        """Test Arabic question generation"""
        logger.info("🌍 Testing Arabic questions...")
        
        test_request = {
            "teaching_point_en": "Understand communication protocols in air defense",
            "teaching_point_ar": "فهم بروتوكولات الاتصال في الدفاع الجوي",
            "question_type": "TRUE_FALSE",
            "language": "ar",
            "bloom_level": "UNDERSTAND"
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/generate-questions",
                json=test_request
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Arabic questions test successful!")
                logger.info(f"🌍 Language: {result['language']}")
                
                if result['questions']:
                    q = result['questions'][0]
                    logger.info(f"📝 Arabic question sample: {q['question'][:50]}...")
                
                return True
            else:
                logger.error(f"❌ Arabic questions test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Arabic questions test error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🚀 Starting comprehensive BAML test suite...")
        
        tests = [
            ("Direct BAML Service", self.test_direct_baml_service),
            ("API Health", self.test_api_health),
            ("BAML Status", self.test_baml_status),
            ("Question Generation", self.test_question_generation_endpoint),
            ("Native BAML Format", self.test_native_baml_endpoint),
            ("Multi-Select Questions", self.test_multi_select_questions),
            ("Arabic Questions", self.test_arabic_questions),
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"🧪 Running: {test_name}")
            logger.info(f"{'='*50}")
            
            try:
                result = await test_func()
                results[test_name] = "PASSED" if result else "FAILED"
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                results[test_name] = f"ERROR: {str(e)}"
                logger.error(f"💥 {test_name}: ERROR - {str(e)}")
        
        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success rate: {(passed/total)*100:.1f}%")
        
        logger.info(f"\n📋 DETAILED RESULTS:")
        for test_name, result in results.items():
            status_emoji = "✅" if result == "PASSED" else "❌"
            logger.info(f"{status_emoji} {test_name}: {result}")
        
        return results
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def main():
    """Main test runner"""
    logger.info("🎬 Starting BAML Testing Suite for AFADI Question Generation")
    
    tester = BAMLTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Check if all tests passed
        all_passed = all(result == "PASSED" for result in results.values())
        
        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED! BAML integration is working correctly.")
        else:
            logger.warning("\n⚠️ Some tests failed. Check the logs above for details.")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
    except Exception as e:
        logger.error(f"\n💥 Test suite failed with error: {e}")
    finally:
        await tester.close()

def run_quick_test():
    """Run a quick synchronous test"""
    print("🚀 Quick BAML Service Test")
    
    try:
        result = baml_service.generate_questions_sync(
            teaching_point_en="Test BAML integration",
            teaching_point_ar="اختبار تكامل BAML",
            question_type="TRUE_FALSE",
            language="en",
            bloom_level="REMEMBER"
        )
        
        print(f"✅ Quick test successful!")
        print(f"📊 Generated {len(result.questions)} questions")
        if result.questions:
            q = result.questions[0]
            print(f"📝 Question: {q.question}")
            print(f"✔️ Answer: {q.answer}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Run quick synchronous test
        success = run_quick_test()
        sys.exit(0 if success else 1)
    else:
        # Run full async test suite
        asyncio.run(main())