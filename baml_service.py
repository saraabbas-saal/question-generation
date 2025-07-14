import logging
from typing import Optional
from baml_client import b
from baml_client.types import QuestionGenerationResult
import asyncio

logger = logging.getLogger(__name__)

class BAMLService:
    """
    Service class for handling BAML-based question generation
    """
    
    def __init__(self):
        self.client = b
        logger.info("✅ BAML Service initialized successfully")
    
    async def generate_questions_async(
        self,
        teaching_point_en: str,
        teaching_point_ar: str = "",
        context: Optional[str] = None,
        question_type: str = "MULTICHOICE",
        number_of_distractors: Optional[int] = None,
        number_of_correct_answers: Optional[int] = None,
        language: str = "en",
        bloom_level: str = "UNDERSTAND"
    ) -> QuestionGenerationResult:
        """
        Generate questions using BAML async client
        
        Args:
            teaching_point_en: Teaching point in English
            teaching_point_ar: Teaching point in Arabic (optional)
            context: Additional context for question generation
            question_type: Type of question (MULTICHOICE, MULTI_SELECT, TRUE_FALSE, TRUE_FALSE_JUSTIFICATION)
            number_of_distractors: Number of incorrect options
            number_of_correct_answers: Number of correct answers (for MULTI_SELECT)
            language: Language for questions (en/ar)
            bloom_level: Bloom's taxonomy level
            
        Returns:
            QuestionGenerationResult: BAML-generated questions
        """
        try:
            logger.info(f"🎯 Generating {question_type} questions in {language}")
            logger.info(f"📚 Teaching point: {teaching_point_en[:100]}...")
            
            # Set defaults based on question type
            if question_type == "MULTICHOICE" and number_of_distractors is None:
                number_of_distractors = 3
            elif question_type == "MULTI_SELECT":
                if number_of_distractors is None:
                    number_of_distractors = 2
                if number_of_correct_answers is None:
                    number_of_correct_answers = 2
            
            # Use Arabic teaching point if language is Arabic but no Arabic version provided
            if language == "ar" and not teaching_point_ar:
                teaching_point_ar = teaching_point_en
            elif not teaching_point_ar:
                teaching_point_ar = ""
            
            # Call BAML function
            result = await self.client.GenerateQuestions(
                teaching_point_en=teaching_point_en,
                teaching_point_ar=teaching_point_ar,
                context=context,
                question_type=question_type,
                number_of_distractors=number_of_distractors,
                number_of_correct_answers=number_of_correct_answers,
                language=language,
                bloom_level=bloom_level
            )
            
            logger.info(f"✅ Successfully generated {len(result.questions)} questions")
            logger.info(f"📊 Question details: {question_type}, {language}, {bloom_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ BAML question generation failed: {str(e)}")
            logger.error(f"🔧 Parameters: type={question_type}, lang={language}, bloom={bloom_level}")
            raise
    
    def generate_questions_sync(
        self,
        teaching_point_en: str,
        teaching_point_ar: str = "",
        context: Optional[str] = None,
        question_type: str = "MULTICHOICE",
        number_of_distractors: Optional[int] = None,
        number_of_correct_answers: Optional[int] = None,
        language: str = "en",
        bloom_level: str = "UNDERSTAND"
    ) -> QuestionGenerationResult:
        """
        Synchronous wrapper for generate_questions_async
        """
        return asyncio.run(self.generate_questions_async(
            teaching_point_en=teaching_point_en,
            teaching_point_ar=teaching_point_ar,
            context=context,
            question_type=question_type,
            number_of_distractors=number_of_distractors,
            number_of_correct_answers=number_of_correct_answers,
            language=language,
            bloom_level=bloom_level
        ))
    
    async def test_connection(self) -> bool:
        """
        Test BAML connection with a simple question
        """
        try:
            logger.info("🔍 Testing BAML connection...")
            
            result = await self.client.GenerateQuestions(
                teaching_point_en="Test connection",
                teaching_point_ar="اختبار الاتصال",
                context=None,
                question_type="TRUE_FALSE",
                number_of_distractors=None,
                number_of_correct_answers=None,
                language="en",
                bloom_level="REMEMBER"
            )
            
            if result and result.questions and len(result.questions) > 0:
                logger.info("✅ BAML connection test successful")
                return True
            else:
                logger.error("❌ BAML connection test failed - no questions generated")
                return False
                
        except Exception as e:
            logger.error(f"❌ BAML connection test failed: {str(e)}")
            return False

# Global instance
baml_service = BAMLService()

# Convenience functions for backward compatibility
async def generate_questions_baml(
    teaching_point_en: str,
    teaching_point_ar: str = "",
    context: Optional[str] = None,
    question_type: str = "MULTICHOICE",
    number_of_distractors: Optional[int] = None,
    number_of_correct_answers: Optional[int] = None,
    language: str = "en",
    bloom_level: str = "UNDERSTAND"
) -> QuestionGenerationResult:
    """Convenience function for async question generation"""
    return await baml_service.generate_questions_async(
        teaching_point_en=teaching_point_en,
        teaching_point_ar=teaching_point_ar,
        context=context,
        question_type=question_type,
        number_of_distractors=number_of_distractors,
        number_of_correct_answers=number_of_correct_answers,
        language=language,
        bloom_level=bloom_level
    )

def generate_questions_baml_sync(
    teaching_point_en: str,
    teaching_point_ar: str = "",
    context: Optional[str] = None,
    question_type: str = "MULTICHOICE",
    number_of_distractors: Optional[int] = None,
    number_of_correct_answers: Optional[int] = None,
    language: str = "en",
    bloom_level: str = "UNDERSTAND"
) -> QuestionGenerationResult:
    """Convenience function for sync question generation"""
    return baml_service.generate_questions_sync(
        teaching_point_en=teaching_point_en,
        teaching_point_ar=teaching_point_ar,
        context=context,
        question_type=question_type,
        number_of_distractors=number_of_distractors,
        number_of_correct_answers=number_of_correct_answers,
        language=language,
        bloom_level=bloom_level
    )