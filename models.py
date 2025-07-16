

# ============================================================================
# models.py - Enhanced Pydantic Models
# ============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

class QuestionType(str, Enum):
    MULTICHOICE = "MULTICHOICE"
    MULTI_SELECT = "MULTI_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    TRUE_FALSE_JUSTIFICATION = "TRUE_FALSE_JUSTIFICATION"

class BloomLevel(str, Enum):
    REMEMBER = "REMEMBER"
    UNDERSTAND = "UNDERSTAND"
    APPLY = "APPLY"
    ANALYZE = "ANALYZE"
    EVALUATE = "EVALUATE"
    CREATE = "CREATE"

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"

class QuestionRequest(BaseModel):
    teaching_point_ar: str = Field(..., description="Teaching point in Arabic")
    teaching_point_en: str = Field(..., description="Teaching point in English")
    context: Optional[str] = Field(None, description="Additional context")
    question_type: QuestionType = Field(..., description="Type of question to generate")
    number_of_distractors: Optional[int] = Field(None, ge=2, le=6, description="Number of incorrect options")
    number_of_correct_answers: Optional[int] = Field(None, ge=1, le=4, description="Number of correct answers for MULTI_SELECT")
    language: Language = Field(default=Language.ENGLISH, description="Generation language")
    bloom_level: BloomLevel = Field(default=BloomLevel.UNDERSTAND, description="Cognitive level")

    @validator('number_of_distractors')
    def validate_distractors(cls, v, values):
        question_type = values.get('question_type')
        if question_type in [QuestionType.MULTICHOICE, QuestionType.MULTI_SELECT] and v is None:
            raise ValueError(f"number_of_distractors required for {question_type}")
        if question_type in [QuestionType.TRUE_FALSE, QuestionType.TRUE_FALSE_JUSTIFICATION] and v is not None:
            return None  # Ignore for true/false questions
        return v

    @validator('number_of_correct_answers')
    def validate_correct_answers(cls, v, values):
        question_type = values.get('question_type')
        if question_type == QuestionType.MULTI_SELECT and v is None:
            raise ValueError("number_of_correct_answers required for MULTI_SELECT")
        if question_type != QuestionType.MULTI_SELECT and v is not None:
            return None  # Ignore for non-multi-select questions
        return v

class QuestionOption(BaseModel):
    key: str = Field(..., description="Option identifier (A, B, C, etc.)")
    value: str = Field(..., description="Option text")

class Question(BaseModel):
    question_number: int
    question: str
    options: List[QuestionOption]
    answer: List[str]  # Support multiple correct answers
    model_answer: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class QuestionResponse(BaseModel):
    questions: List[Question]
    teaching_point: str
    question_type: QuestionType
    language: Language
    bloom_level: BloomLevel
    generation_metadata: Dict[str, Any] = {}
