
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Query(BaseModel):
    prompt: str = Field(..., description="The prompt for text generation")

class QuestionRequest(BaseModel):
    teaching_point_ar: str = Field(..., description="The teaching point to generate questions from (in arabic lang)")
    teaching_point_en: str = Field(..., description="The teaching point to generate questions from (in english lang)")
    question_type: str = Field(..., description="Type of questions: 'MULTICHOICE', 'MULTI_SELECT', 'TRUE_FALSE', or 'TRUE_FALSE_JUSTIFICATION'")
    number_of_distractors: Optional[int] = Field(None, ge=2, le=6, description="Number of distractors for MULTICHOICE and MULTI_SELECT questions (required for these types, ignored for True/False)")
    number_of_correct_answers: Optional[int] = Field(None, ge=1, le=4, description="Number of correct answers for MULTI_SELECT questions (required for MULTI_SELECT, ignored for others)")
    language: str = Field(default="en", description="Language for question generation")
    bloom_level: str = Field(default="Understand", description="Bloom's taxonomy level")

class Question(BaseModel):
    question_number: int
    question: str
    options: List[dict]  # Always present, even for TRUE_FALSE (will be ["True", "False"])
    answer: List[str]  # The answer field
    model_answer: Optional[str] = None  # Added: For TRUE_FALSE_JUSTIFICATION

class QuestionResponse(BaseModel):
    questions: List[Question]
    teaching_point: str
    question_type: str
    language: str
    bloom_level: str