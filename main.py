print("=== BAML-ONLY AFADI QUESTION GENERATION API ===")
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging
from baml_service import baml_service
from baml_client.types import QuestionGenerationResult, GeneratedQuestion, QuestionOption

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AFADI Question Generation API (BAML)",
    description="API for generating military assessment questions using BAML only",
    version="3.0.0"
)

# Pydantic models for API requests (keeping these minimal for FastAPI)
class QuestionRequest(BaseModel):
    teaching_point_en: str
    teaching_point_ar: str = ""
    context: Optional[str] = None
    question_type: str = "MULTICHOICE"
    number_of_distractors: Optional[int] = None
    number_of_correct_answers: Optional[int] = None
    language: str = "en"
    bloom_level: str = "UNDERSTAND"

class LegacyQuery(BaseModel):
    prompt: str

# Helper function to convert BAML result to legacy format
def convert_baml_to_legacy_format(baml_result: QuestionGenerationResult) -> Dict[str, Any]:
    """
    Convert BAML QuestionGenerationResult to legacy API format for backward compatibility
    """
    legacy_questions = []
    
    for question in baml_result.questions:
        legacy_question = {
            "question_number": question.question_number,
            "question": question.question,
            "options": [{"key": opt.key, "value": opt.value} for opt in question.options],
            "answer": question.answer,
            "confidence_score": 0.95  # Default confidence score
        }
        
        # Add model_answer if present (for TRUE_FALSE_JUSTIFICATION)
        if question.model_answer:
            legacy_question["model_answer"] = question.model_answer
            
        legacy_questions.append(legacy_question)
    
    return {
        "questions": legacy_questions,
        "teaching_point": baml_result.teaching_point,
        "question_type": baml_result.question_type,
        "language": baml_result.language,
        "bloom_level": baml_result.bloom_level,
        "success": True,
        "total_questions": len(legacy_questions)
    }

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AFADI Question Generation API with BAML-only is running",
        "version": "3.0.0",
        "baml_enabled": True,
        "legacy_support": True
    }

@app.post("/generate-questions", response_model=Dict[str, Any])
async def generate_questions(request: QuestionRequest):
    """
    Generate exactly 3 assessment questions using BAML
    Returns legacy format for backward compatibility
    """
    try:
        # Validate question type
        valid_types = ["MULTICHOICE", "MULTI_SELECT", "TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"]
        if request.question_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question_type. Must be one of: {', '.join(valid_types)}"
            )
  
        # Validate MULTI_SELECT parameters
        if request.question_type == "MULTI_SELECT":
            if request.number_of_correct_answers is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_correct_answers is required for MULTI_SELECT questions"
                )
            if request.number_of_distractors is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_distractors is required for MULTI_SELECT questions"
                )
        
        # Validate MULTICHOICE parameters
        if request.question_type == "MULTICHOICE":
            if request.number_of_distractors is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_distractors is required for MULTICHOICE questions"
                )
        
        # Generate questions using BAML
        logger.info(f"🎯 Generating {request.question_type} questions via BAML")
        
        baml_result = await baml_service.generate_questions_async(
            teaching_point_en=request.teaching_point_en,
            teaching_point_ar=request.teaching_point_ar,
            context=request.context,
            question_type=request.question_type,
            number_of_distractors=request.number_of_distractors,
            number_of_correct_answers=request.number_of_correct_answers,
            language=request.language,
            bloom_level=request.bloom_level
        )
        
        # Convert to legacy format for backward compatibility
        legacy_response = convert_baml_to_legacy_format(baml_result)
        
        logger.info(f"✅ Successfully generated {len(baml_result.questions)} questions via BAML")
        return legacy_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in generate_questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.post("/generate-questions-baml", response_model=Dict[str, Any])
async def generate_questions_baml_native(request: QuestionRequest):
    """
    Generate questions using BAML - returns native BAML format
    """
    try:
        # Same validation as above
        valid_types = ["MULTICHOICE", "MULTI_SELECT", "TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"]
        if request.question_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Generate questions using BAML
        logger.info(f"🎯 Generating {request.question_type} questions via BAML (native format)")
        
        baml_result = await baml_service.generate_questions_async(
            teaching_point_en=request.teaching_point_en,
            teaching_point_ar=request.teaching_point_ar,
            context=request.context,
            question_type=request.question_type,
            number_of_distractors=request.number_of_distractors,
            number_of_correct_answers=request.number_of_correct_answers,
            language=request.language,
            bloom_level=request.bloom_level
        )
        
        # Return BAML result directly (will be auto-serialized)
        logger.info(f"✅ Successfully generated {len(baml_result.questions)} questions via BAML")
        return baml_result.model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in generate_questions_baml_native: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.post("/generate", response_model=Dict[str, Any])
async def generate_text(query: LegacyQuery):
    """
    Legacy endpoint - now powered by BAML
    Generate text based on a custom prompt
    """
    try:
        # For backward compatibility, we'll try to extract teaching point from prompt
        # and generate a simple question
        logger.info("📤 Legacy endpoint called - converting to BAML")
        
        result = await baml_service.generate_questions_async(
            teaching_point_en=query.prompt,
            teaching_point_ar="",
            context=None,
            question_type="MULTICHOICE",
            number_of_distractors=3,
            number_of_correct_answers=None,
            language="en",
            bloom_level="UNDERSTAND"
        )
        
        # Convert to simple text response for legacy compatibility
        questions_text = ""
        for i, q in enumerate(result.questions, 1):
            questions_text += f"Question {i}: {q.question}\n"
            for opt in q.options:
                questions_text += f"{opt.key}) {opt.value}\n"
            questions_text += f"Answer: {', '.join(q.answer)}\n\n"
        
        return {"response": questions_text.strip()}
        
    except Exception as e:
        logger.error(f"❌ Error in legacy generate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Comprehensive health check including BAML connectivity"""
    try:
        # Test BAML connection
        baml_status = await baml_service.test_connection()
        
        return {
            "status": "healthy" if baml_status else "degraded",
            "service": "AFADI Question Generation API (BAML-only)",
            "version": "3.0.0",
            "baml_enabled": True,
            "baml_connection": "ok" if baml_status else "failed",
            "legacy_api_support": True
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "AFADI Question Generation API (BAML-only)",
            "version": "3.0.0",
            "baml_enabled": True,
            "baml_connection": "error",
            "error": str(e)
        }

@app.get("/baml-status")
async def baml_status():
    """Detailed BAML status check"""
    try:
        connection_ok = await baml_service.test_connection()
        
        return {
            "baml_client_available": True,
            "connection_test": "passed" if connection_ok else "failed",
            "generate_questions_function": "available",
            "supported_question_types": [
                "MULTICHOICE", 
                "MULTI_SELECT", 
                "TRUE_FALSE", 
                "TRUE_FALSE_JUSTIFICATION"
            ],
            "supported_languages": ["en", "ar"],
            "supported_bloom_levels": [
                "REMEMBER", "UNDERSTAND", "APPLY", 
                "ANALYZE", "EVALUATE", "CREATE"
            ]
        }
    except Exception as e:
        return {
            "baml_client_available": False,
            "error": str(e),
            "suggestion": "Check BAML configuration and LLM connectivity"
        }

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=8888,
        workers=1,
        log_level="info",
        reload=True
    )