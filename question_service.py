
# ============================================================================
# question_service.py - Main Service Layer
# ============================================================================
import time
import logging
from typing import Dict

from models import QuestionRequest, QuestionResponse, QuestionType, Language
from llm_client import LLMClient
from question_generators import (
    MultipleChoiceGenerator, 
    MultiSelectGenerator, 
    TrueFalseGenerator, 
    TrueFalseJustificationGenerator
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuestionGenerationService:
    """Main service for generating questions with routing to specialized generators"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.generators = {
            QuestionType.MULTICHOICE: MultipleChoiceGenerator(llm_client),
            QuestionType.MULTI_SELECT: MultiSelectGenerator(llm_client),
            QuestionType.TRUE_FALSE: TrueFalseGenerator(llm_client),
            QuestionType.TRUE_FALSE_JUSTIFICATION: TrueFalseJustificationGenerator(llm_client)
        }
    
    def generate_questions(self, request: QuestionRequest) -> QuestionResponse:
        """Generate questions using appropriate specialized generator"""
        start_time = time.time()
        
        try:
            logger.info(f"Generating {request.question_type} questions in {request.language}")
            
            generator = self.generators.get(request.question_type)
            if not generator:
                raise ValueError(f"Unsupported question type: {request.question_type}")
            
            questions = generator.generate_questions(request)
            
            # Ensure exactly 3 questions
            if len(questions) < 3:
                logger.warning(f"Only generated {len(questions)} questions, padding to 3")
                while len(questions) < 3:
                    questions.extend(generator._create_fallback_questions(request))
            
            questions = questions[:3]  # Ensure exactly 3
            
            generation_time = time.time() - start_time
            
            response = QuestionResponse(
                questions=questions,
                teaching_point=generator._get_teaching_point(request),
                question_type=request.question_type,
                language=request.language,
                bloom_level=request.bloom_level,
                generation_metadata={
                    "generation_time_seconds": round(generation_time, 2),
                    "generator_type": type(generator).__name__,
                    "average_confidence": sum(q.confidence_score or 0 for q in questions) / len(questions)
                }
            )
            
            logger.info(f"Successfully generated {len(questions)} questions in {generation_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise
