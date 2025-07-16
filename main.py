
# ============================================================================
# main.py - Enhanced FastAPI Application
# ============================================================================
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging

from models import QuestionRequest, QuestionResponse
from llm_client import LLMClient
from question_service import QuestionGenerationService

# # Global service instance
# llm_client = None
# question_service = None
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global llm_client, question_service
    
    # Startup
    logger.info("Initializing AFADI Question Generation Service...")
    llm_client = LLMClient()
    
    # Test LLM connection
    if not llm_client.test_connection():
        logger.error("Failed to connect to LLM service")
        raise RuntimeError("LLM service unavailable")
    
    question_service = QuestionGenerationService(llm_client)
    logger.info("Service initialization complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service...")

app = FastAPI(
    title="AFADI Military Question Generation API",
    description="Advanced question generation system for Air Force Defense Institute",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_question_service() -> QuestionGenerationService:
    """Dependency injection for question service"""
    if question_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return question_service

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "AFADI Question Generation API v2.0",
        "status": "operational",
        "features": ["Multiple Choice", "Multi-Select", "True/False", "True/False with Justification"]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        llm_status = llm_client.test_connection() if llm_client else False
        return {
            "status": "healthy" if llm_status else "degraded",
            "llm_connection": llm_status,
            "service": "AFADI Question Generation API",
            "version": "2.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "AFADI Question Generation API",
            "version": "2.0.0"
        }

@app.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions(
    request: QuestionRequest,
    service: QuestionGenerationService = Depends(get_question_service)
):
    """Generate military assessment questions with specialized routing"""
    try:
        logger.info(f"Request received: {request.question_type} in {request.language}")
        
        response = service.generate_questions(request)
        
        logger.info(f"Successfully generated {len(response.questions)} questions")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.get("/question-types")
async def get_question_types():
    """Get available question types and their requirements"""
    return {
        "question_types": {
            "MULTICHOICE": {
                "description": "Single correct answer with multiple distractors",
                "required_params": ["number_of_distractors"],
                "cognitive_levels": ["REMEMBER", "UNDERSTAND", "APPLY"]
            },
            "MULTI_SELECT": {
                "description": "Multiple correct answers from options",
                "required_params": ["number_of_distractors", "number_of_correct_answers"],
                "cognitive_levels": ["APPLY", "ANALYZE", "EVALUATE"]
            },
            "TRUE_FALSE": {
                "description": "Simple true/false statement",
                "required_params": [],
                "cognitive_levels": ["REMEMBER", "UNDERSTAND"]
            },
            "TRUE_FALSE_JUSTIFICATION": {
                "description": "True/false with detailed explanation",
                "required_params": [],
                "cognitive_levels": ["UNDERSTAND", "ANALYZE", "EVALUATE"]
            }
        },
        "languages": ["en", "ar"],
        "bloom_levels": ["REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE"]
    }



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8088,
        reload=True,
        log_level="info"
    )