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
    teaching_point: str = Field(..., description="The teaching point to generate questions from")
    question_type: str = Field(..., description="Type of questions: 'Multiple Choice', 'Multi-Select', 'True or False', or 'True or False with Justification'")
    number_of_distractors: Optional[int] = Field(None, ge=2, le=6, description="Number of distractors for Multiple Choice and Multi-Select (total options = distractors + correct answers)")
    number_of_correct_answers: Optional[int] = Field(None, ge=1, le=4, description="Number of correct answers for Multi-Select questions")
    language: str = Field(default="english", description="Language for question generation")
    bloom_level: str = Field(default="Understand", description="Bloom's taxonomy level")

class Question(BaseModel):
    question_number: int
    question_text: str
    question_type: str
    options: List[str]  # Always present, even for True or False (will be ["True", "False"])
    correct_answer: Optional[str] = None  # Single correct answer for MCQ and True or False
    correct_answers: Optional[List[str]] = None  # Multiple correct answers for Multi-Select
    teaching_points_covered: str  # Teaching points covered in this question
    model_answer: Optional[str] = None  # For True or False with Justification

class QuestionResponse(BaseModel):
    questions: List[Question]
    teaching_point: str
    question_type: str
    language: str
    bloom_level: str
    total_questions: int = 3

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
        if request.question_type == "Multiple Choice" and request.number_of_distractors is None:
            raise HTTPException(
                status_code=400, 
                detail="number_of_distractors is required for Multiple Choice questions"
            )
        
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
            bloom_level=request.bloom_level,
            total_questions=len(parsed_questions)
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
Your task is to: Understand the semantic meaning of the teaching point. Apply Bloom’s Taxonomy to determine appropriate cognitive levels (e.g., understand, apply, analyze). 
Generate four types of questions: Five Multiple Choice Question (MCQ) Guidelines: AFADI refers to the Air Force Defense and Institute — always maintain relevance to this context. Avoid simply rephrasing the teaching point. Be creative and focus on implications, applications, comparisons, and conceptual understanding. Use military air defense scenarios or terminology where appropriate. Ensure all questions are clear, relevant, and test different levels of cognitive ability. Teaching Point: “Describe the tenets of airpower”

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
3. Correct answer(s)
4. Teaching points covered (specific aspects of the main teaching point this question addresses)
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
Correct Answer: [Option A]
Teaching Points Covered: [Specific aspects of the teaching point this question addresses]
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
Correct Answers: [Option A, Option B]
Teaching Points Covered: [Specific aspects of the teaching point this question addresses]
"""
    
    elif question_type == "True or False":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Correct Answer: [A or B]
Teaching Points Covered: [Specific aspects of the teaching point this question addresses]
"""
    
    elif question_type == "True or False with Justification":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Correct Answer: [A or B]
Teaching Points Covered: [Specific aspects of the teaching point this question addresses]
Model Answer: [Detailed justification explaining why the answer is correct]
"""

def parse_generated_questions(generated_text: str, question_type: str, teaching_point: str,
                            number_of_distractors: Optional[int] = None, 
                            number_of_correct_answers: Optional[int] = None) -> List[Question]:
    """
    Parse the generated text into structured Question objects
    """
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
        
        # Parse each question block
        for i, block in enumerate(question_blocks[:3], 1):  # Ensure only 3 questions
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
        
        # Parse answers and other fields
        correct_answer = None
        correct_answers = []
        teaching_points_covered = ""
        model_answer = None
        
        for line in lines:
            if line.startswith('Correct Answer:'):
                correct_answer = line.split(':', 1)[1].strip()
            elif line.startswith('Correct Answers:'):
                correct_answers = [ans.strip() for ans in line.split(':', 1)[1].split(',')]
            elif line.startswith('Teaching Points Covered:'):
                teaching_points_covered = line.split(':', 1)[1].strip()
            elif line.startswith('Model Answer:'):
                model_answer = line.split(':', 1)[1].strip()
        
        # Default teaching points covered if not found
        if not teaching_points_covered:
            teaching_points_covered = f"Application of: {teaching_point}"
        
        return Question(
            question_number=question_number,
            question_text=question_text,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer if question_type != "Multi-Select" else None,
            correct_answers=correct_answers if question_type == "Multi-Select" else None,
            teaching_points_covered=teaching_points_covered,
            model_answer=model_answer
        )
    
    except Exception as e:
        logger.error(f"Error parsing single question: {e}")
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
            question_text=f"Question {question_number} - parsing error occurred",
            question_type=question_type,
            options=options,
            correct_answer="A",
            teaching_points_covered=f"Related to: {teaching_point}"
        )
    
    elif question_type == "Multi-Select":
        total_options = (number_of_distractors or 2) + (number_of_correct_answers or 2)
        options = [f"Option {chr(65 + i)}" for i in range(total_options)]
        correct_count = number_of_correct_answers or 2
        correct_answers = [chr(65 + i) for i in range(correct_count)]
        return Question(
            question_number=question_number,
            question_text=f"Question {question_number} - parsing error occurred",
            question_type=question_type,
            options=options,
            correct_answers=correct_answers,
            teaching_points_covered=f"Related to: {teaching_point}"
        )
    
    else:  # True or False or True or False with Justification
        return Question(
            question_number=question_number,
            question_text=f"Question {question_number} - parsing error occurred",
            question_type=question_type,
            options=["True", "False"],
            correct_answer="A",
            teaching_points_covered=f"Related to: {teaching_point}",
            model_answer="This question had parsing issues." if question_type == "True or False with Justification" else None
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