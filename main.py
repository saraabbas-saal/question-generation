from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uvicorn
import logging
from llm_utils import get_llm_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AFADI Question Generation API",
    description="API for generating military assessment questions",
    version="1.0.0"
)

class Query(BaseModel):
    prompt: str = Field(..., description="The prompt for text generation")

class QuestionRequest(BaseModel):
    teaching_point_ar: str = Field(..., description="The teaching point to generate questions from (in arabic lang)")
    teaching_point_en: str = Field(..., description="The teaching point to generate questions from (in english lang)")
    question_type: str = Field(..., description="Type of questions: 'Multiple Choice', 'Multi-Select', 'True or False', or 'True or False with Justification'")
    number_of_distractors: Optional[int] = Field(None, ge=2, le=6, description="Number of distractors for Multiple Choice and Multi-Select questions (required for these types, ignored for True/False)")
    number_of_correct_answers: Optional[int] = Field(None, ge=1, le=4, description="Number of correct answers for Multi-Select questions (required for Multi-Select, ignored for others)")
    language: str = Field(default="english", description="Language for question generation")
    bloom_level: str = Field(default="Understand", description="Bloom's taxonomy level")

class Question(BaseModel):
    question_number: int
    question: str
    options: List[str]  # Always present, even for True or False (will be ["True", "False"])
    answer: str  # The answer field
    model_answer: Optional[str] = None  # Added: For True or False with Justification

class QuestionResponse(BaseModel):
    questions: List[Question]
    teaching_point: str
    question_type: str
    language: str
    bloom_level: str

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
        valid_types = ["Multiple Choice", "Multi-Select", "True or False", "True or False with Justification"]
        if request.question_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate Multi-Select parameters
        if request.question_type == "Multi-Select":
            if request.number_of_correct_answers is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_correct_answers is required for Multi-Select questions"
                )
            if request.number_of_distractors is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_distractors is required for Multi-Select questions"
                )
        
        # Validate Multiple Choice parameters
        if request.question_type == "Multiple Choice":
            if request.number_of_distractors is None:
                raise HTTPException(
                    status_code=400, 
                    detail="number_of_distractors is required for Multiple Choice questions"
                )
        
        # Validate True/False parameters - number_of_distractors should be ignored
        if request.question_type in ["True or False", "True or False with Justification"]:
            if request.number_of_distractors is not None:
                logger.warning(f"number_of_distractors ({request.number_of_distractors}) will be ignored for {request.question_type} questions")
            if request.number_of_correct_answers is not None:
                logger.warning(f"number_of_correct_answers ({request.number_of_correct_answers}) will be ignored for {request.question_type} questions")
        
        # Create the prompt using the helper function
        prompt = set_map_prompt(
            teaching_point=request.teaching_point,
            question_type=request.question_type,
            number_of_distractors=request.number_of_distractors,
            number_of_correct_answers=request.number_of_correct_answers,
            language=request.language,
            bloom_level=request.bloom_level
        )
        
        # Generate questions using LLM
        generated_response = get_llm_response(prompt, max_tokens=2500)
        
        # Parse the generated response into structured questions
        parsed_questions = parse_generated_questions(
            generated_response, 
            request.question_type,
            request.teaching_point,
            request.number_of_distractors,
            request.number_of_correct_answers
        )
        
        # Return structured response
        return QuestionResponse(
            questions=parsed_questions,
            teaching_point=request.teaching_point,
            question_type=request.question_type,
            language=request.language,
            bloom_level=request.bloom_level
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

def set_map_prompt(teaching_point: str, question_type: str, number_of_distractors: Optional[int], 
                  number_of_correct_answers: Optional[int], language: str, bloom_level: str) -> str:
    """
    Creates a prompt template for question generation based on specific requirements
    """
    
    # Calculate total options for Multiple Choice and Multi-Select
    if question_type == "Multiple Choice":
        total_options = number_of_distractors + 1  # distractors + 1 correct answer
        options_text = f"Generate exactly {total_options} options (A, B, C, D, etc.) with exactly 1 correct answer."
    elif question_type == "Multi-Select":
        total_options = number_of_distractors + number_of_correct_answers
        options_text = f"Generate exactly {total_options} options (A, B, C, D, etc.) with exactly {number_of_correct_answers} correct answers."
    elif question_type in ["True or False", "True or False with Justification"]:
        options_text = "Generate exactly 2 options: A) True, B) False"
    
    # Justification text for True or False with Justification
    justification_text = ""
    if question_type == "True or False with Justification":
        justification_text = "\nModel Answer: [Detailed justification explaining why the answer is correct]"
    
    # Question type specific formatting instructions
    format_instructions = get_format_instructions(question_type)
    
    map_prompt_template = f"""
You are a smart instructor for the Air Force Defense and Institute (AFADI) generating military assessment questions.

You are an AI assistant designed to generate assessment questions for the military Air Force Defense and Institute (AFADI). 
You will be given a teaching point, which is linked to a specific military concept or learning objective. 
Your task is to: Understand the semantic meaning of the teaching point. Apply Bloom's Taxonomy to determine appropriate cognitive levels (e.g., understand, apply, analyze). 
Generate assessment questions following the specific format below.

IMPORTANT: Generate exactly 3 questions, no more, no less.

Parameters:
- Teaching Point: {teaching_point}
- Question Type: {question_type}
- Language: {language}
- Bloom's Taxonomy Level: {bloom_level}

Requirements:
- {options_text}
- Focus on {bloom_level} cognitive level of Bloom's Taxonomy
- Each question must be directly related to the teaching point
- Use military air defense context and AFADI scenarios
- Make each question unique and test different aspects

{format_instructions}

For each question, you must include:
1. Question text
2. All options (labeled A, B, C, etc.)
3. Answer(s)
4. [OPTIONAL] Model Answer in the case of True or False with justification
{justification_text}

Generate exactly 3 questions in {language} language following the specified format.
"""

    return map_prompt_template.strip()

def get_format_instructions(question_type: str) -> str:
    """Get specific formatting instructions based on question type"""
    
    if question_type == "Multiple Choice":
        return """
Format each question as:
Question [Number]: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
[Add more options as needed based on number of distractors]
Answer: [A, B, C, or D]
"""
    
    elif question_type == "Multi-Select":
        return """
Format each question as:
Question [Number]: [Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
[Add more options as needed]
Answer: [A, C] (multiple letters separated by commas)
"""
    
    elif question_type == "True or False":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Answer: [A or B]
"""
    
    elif question_type == "True or False with Justification":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Answer: [A or B]
Model Answer: [Detailed justification explaining why the answer is True or False]
"""

def parse_generated_questions(generated_text: str, question_type: str, teaching_point: str,
                            number_of_distractors: Optional[int] = None, 
                            number_of_correct_answers: Optional[int] = None) -> List[Question]:
    """
    Parse the generated text into structured Question objects
    """
    logger.info(f"Parsing generated text: {generated_text[:200]}...")
    questions = []
    
    try:
        # Split by question numbers
        question_blocks = []
        lines = generated_text.strip().split('\n')
        current_block = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Question ') and ':' in line:
                if current_block:
                    question_blocks.append('\n'.join(current_block))
                current_block = [line]
            elif current_block:
                current_block.append(line)
        
        if current_block:
            question_blocks.append('\n'.join(current_block))
        
        logger.info(f"Found {len(question_blocks)} question blocks")
        
        # Parse each question block
        for i, block in enumerate(question_blocks[:3], 1):  # Ensure only 3 questions
            logger.info(f"Parsing question {i}: {block[:100]}...")
            question = parse_single_question(block, question_type, i, teaching_point)
            if question:
                questions.append(question)
        
        # Ensure we have exactly 3 questions
        while len(questions) < 3:
            questions.append(create_fallback_question(
                len(questions) + 1, question_type, teaching_point, 
                number_of_distractors, number_of_correct_answers
            ))
    
    except Exception as e:
        logger.error(f"Error parsing questions: {e}")
        # Return default questions if parsing fails
        for i in range(3):
            questions.append(create_fallback_question(
                i + 1, question_type, teaching_point, 
                number_of_distractors, number_of_correct_answers
            ))
    
    return questions[:3]  # Ensure exactly 3 questions

def parse_single_question(block: str, question_type: str, question_number: int, teaching_point: str) -> Optional[Question]:
    """Parse a single question block into a Question object"""
    
    try:
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        logger.info(f"Parsing lines: {lines}")
        
        # Extract question text
        question_text = ""
        for line in lines:
            if line.startswith('Question ') and ':' in line:
                question_text = line.split(':', 1)[1].strip()
                break
        
        # Parse options
        options = []
        for line in lines:
            if line.startswith(('A)', 'B)', 'C)', 'D)', 'E)', 'F)')):
                options.append(line[2:].strip())
        
        # Ensure True or False questions always have exactly 2 options
        if question_type in ["True or False", "True or False with Justification"]:
            options = ["True", "False"]
        
        # Parse answer field
        answer = None
        for line in lines:
            if line.startswith('Answer:'):
                answer = line.split(':', 1)[1].strip()
                break
        
        # Parse model answer field (for True or False with Justification)
        model_answer = None
        if question_type == "True or False with Justification":
            for line in lines:
                if line.startswith('Model Answer:'):
                    model_answer = line.split(':', 1)[1].strip()
                    break
        
        # Default answer if not found
        if not answer:
            answer = "A"  # Default to first option
        
        logger.info(f"Parsed question: text='{question_text}', options={options}, answer='{answer}', model_answer='{model_answer}'")
        
        return Question(
            question_number=question_number,
            question=question_text,
            options=options,
            answer=answer,
            model_answer=model_answer  # Added: Include model_answer
        )
    
    except Exception as e:
        logger.error(f"Error parsing single question: {e}")
        logger.error(f"Block content: {block}")
        return None

def create_fallback_question(question_number: int, question_type: str, teaching_point: str,
                           number_of_distractors: Optional[int], 
                           number_of_correct_answers: Optional[int]) -> Question:
    """Create a fallback question when parsing fails"""
    
    if question_type == "Multiple Choice":
        total_options = (number_of_distractors or 3) + 1
        options = [f"Option {chr(65 + i)}" for i in range(total_options)]
        return Question(
            question_number=question_number,
            question=f"Question {question_number} - parsing error occurred",
            options=options,
            answer="A",
            model_answer=None  # No model answer for Multiple Choice
        )
    
    elif question_type == "Multi-Select":
        total_options = (number_of_distractors or 2) + (number_of_correct_answers or 2)
        options = [f"Option {chr(65 + i)}" for i in range(total_options)]
        return Question(
            question_number=question_number,
            question=f"Question {question_number} - parsing error occurred",
            options=options,
            answer="A, B",  # Multi-select format
            model_answer=None  # No model answer for Multi-Select
        )
    
    else:  # True or False or True or False with Justification
        model_answer = None
        if question_type == "True or False with Justification":
            model_answer = "This question had parsing issues - unable to provide detailed justification."
        
        return Question(
            question_number=question_number,
            question=f"Question {question_number} - parsing error occurred",
            options=["True", "False"],
            answer="A",
            model_answer=model_answer  # Include model answer for justification type
        )

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