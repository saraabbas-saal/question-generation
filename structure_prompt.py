from typing import Optional, List, Dict, Any
import uvicorn
import logging
from pydantic_classes import Question, QuestionRequest, Query, QuestionResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def get_format_instructions(question_type: str) -> str:
    """Get specific formatting instructions based on question type"""
    
    if question_type == "MULTICHOICE":
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
    
    elif question_type == "MULTI_SELECT":
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
    
    elif question_type == "TRUE_FALSE":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Answer: [A or B]
"""
    
    elif question_type == "TRUE_FALSE_JUSTIFICATION":
        return """
Format each question as:
Question [Number]: [Question text]
A) True
B) False
Answer: [A or B]
Model Answer: [Detailed justification explaining why the answer is TRUE_FALSE]
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
            if line.startswith(('A) ', 'B) ', 'C) ', 'D) ', 'E) ', 'F) ')):
                # options.append(line[2:].strip())
                options.append(
                { "key": line[0:1],
                 "value": line[2:].strip()
                }
                 )
        
        # Ensure TRUE_FALSE questions always have exactly 2 options
        if question_type in ["TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"]:
            options = [
                { "key": "A",
                 "value": "True"
                 }, 
                 { "key": "B", 
                 "value": "False" }
                ]
        
        # Parse answer field
        answer = None
        for line in lines:
            if line.startswith('Answer:'):
                answer = line.split(':', -1)[1].split(',',-1)
                # logger.info(f"answerssssssssssss: {answer}")
                answer= [i.strip() for i in answer]
                break
        
        # Parse model answer field (for TRUE_FALSE_JUSTIFICATION)
        model_answer = None
        if question_type == "TRUE_FALSE_JUSTIFICATION":
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


def set_map_prompt(teaching_point: str, question_type: str, number_of_distractors: Optional[int], 
                  number_of_correct_answers: Optional[int], language: str, bloom_level: str) -> str:
    """
    Creates a prompt template for question generation based on specific requirements
    """
    
    # Calculate total options for MULTICHOICE and MULTI_SELECT
    if question_type == "MULTICHOICE":
        total_options = number_of_distractors + 1  # distractors + 1 correct answer
        options_text = f"Generate exactly {total_options} options (A, B, C, D, etc.) with exactly 1 correct answer."
    elif question_type == "MULTI_SELECT":
        total_options = number_of_distractors + number_of_correct_answers
        options_text = f"Generate exactly {total_options} options (A, B, C, D, etc.) with exactly {number_of_correct_answers} correct answers."
    elif question_type in ["TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"]:
        options_text = "Generate exactly 2 options: A) True, B) False"
    
    # Justification text for TRUE_FALSE_JUSTIFICATION
    justification_text = ""
    if question_type == "TRUE_FALSE_JUSTIFICATION":
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
4. [OPTIONAL] Model Answer in the case of TRUE_FALSE_JUSTIFICATION
{justification_text}

Generate exactly 3 questions in {language} language following the specified format.
"""

    return map_prompt_template.strip()
