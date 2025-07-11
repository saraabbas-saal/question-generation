print("=== FILE RELOADED ===")
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import logging
from llm_utils import get_llm_response
from structure_prompt import get_format_instructions, parse_generated_questions, parse_single_question, set_map_prompt
from pydantic_classes import Question, QuestionRequest, Query, QuestionResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AFADI Question Generation API",
    description="API for generating military assessment questions",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AFADI Question Generation API is running"}

@app.post("/generate", response_model=dict)
async def generate_text(query: Query):
    """
    Generate text based on a custom prompt
    """
    try:
        response = get_llm_response(query.prompt)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in generate_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

@app.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions(request: QuestionRequest):
    """
    Generate exactly 3 assessment questions based on teaching points for AFADI
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
                    detail="number_of_distractors is required for Multiple Choice questions"
                )
        
        # # Validate True/False parameters - number_of_distractors should be ignored
        # if request.question_type in ["TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"]:
        #     if request.number_of_distractors is not None:
        #         logger.warning(f"number_of_distractors ({request.number_of_distractors}) will be ignored for {request.question_type} questions")
        #     if request.number_of_correct_answers is not None:
        #         logger.warning(f"number_of_correct_answers ({request.number_of_correct_answers}) will be ignored for {request.question_type} questions")
        
        # Create the prompt using the helper function
        
        if request.language == 'ar':
            teaching_point=request.teaching_point_ar
            lang= 'arabic'
        elif request.language== 'en':
            teaching_point=request.teaching_point_en
            lang= 'english'
    
        prompt = set_map_prompt(
            teaching_point=teaching_point,
            context= request.context,
            question_type=request.question_type,
            number_of_distractors=request.number_of_distractors,
            number_of_correct_answers=request.number_of_correct_answers,
            language=lang,
            bloom_level=request.bloom_level
        )
        
        # Generate questions using LLM
        generated_response = get_llm_response(prompt, max_tokens=2500)
        
        # Parse the generated response into structured questions
        parsed_questions = parse_generated_questions(
            generated_response, 
            request.question_type,
            teaching_point,
            request.number_of_distractors,
            request.number_of_correct_answers
        )
        
        # Return structured response
        return QuestionResponse(
            questions=parsed_questions,
            teaching_point=teaching_point,
            question_type=request.question_type,
            language=lang,#request.language,
            bloom_level=request.bloom_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")


# def create_fallback_question(question_number: int, question_type: str, teaching_point: str,
#                            number_of_distractors: Optional[int], 
#                            number_of_correct_answers: Optional[int]) -> Question:
#     """Create a fallback question when parsing fails"""
    
#     if question_type == "MULTICHOICE":
#         total_options = (number_of_distractors or 3) + 1
#         options = [f"Option {chr(65 + i)}" for i in range(total_options)]
#         return Question(
#             question_number=question_number,
#             question=f"Question {question_number} - parsing error occurred",
#             options=options,
#             answer="A",
#             model_answer=None  # No model answer for MULTICHOICE
#         )
    
#     elif question_type == "MULTI_SELECT":
#         total_options = (number_of_distractors or 2) + (number_of_correct_answers or 2)
#         options = [f"Option {chr(65 + i)}" for i in range(total_options)]
#         return Question(
#             question_number=question_number,
#             question=f"Question {question_number} - parsing error occurred",
#             options=options,
#             answer="A, B",  # MULTI_SELECT format
#             model_answer=None  # No model answer for MULTI_SELECT
#         )
    
#     else:  # TRUE_FALSE or TRUE_FALSE_JUSTIFICATION
#         model_answer = None
#         if question_type == "TRUE_FALSE_JUSTIFICATION":
#             model_answer = "This question had parsing issues - unable to provide detailed justification."
        
#         return Question(
#             question_number=question_number,
#             question=f"Question {question_number} - parsing error occurred",
#             options=[
#                 { "key": "A)",
#                  "value": "True"
#                  }, 
#                  { "key": "B)", 
#                  "value": "False" }
#                 ],
#             answer="A",
#             model_answer=model_answer  # Include model answer for justification type
#         )

# Health check for the service
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "AFADI Question Generation API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Run with uvicorn with optimized settings
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=8888,
        workers=1,
        log_level="info",
        reload=True
    )