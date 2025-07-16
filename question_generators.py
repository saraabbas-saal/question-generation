
# ============================================================================
# question_generators.py - Specialized Question Generation Strategies
# ============================================================================
import json
import re
import logging
from abc import ABC, abstractmethod
from typing import List

from models import QuestionRequest, Question, QuestionOption, QuestionType, Language
from llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class QuestionGenerator(ABC):
    """Base class for question generators"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    @abstractmethod
    def generate_prompt(self, request: QuestionRequest) -> str:
        """Generate specialized prompt for question type"""
        pass
    
    @abstractmethod
    def parse_response(self, response: str, request: QuestionRequest) -> List[Question]:
        """Parse LLM response into Question objects"""
        pass
    
    def generate_questions(self, request: QuestionRequest) -> List[Question]:
        """Main generation method"""
        try:
            prompt = self.generate_prompt(request)
            logger.info(f"Generated prompt for {request.question_type}")
            
            response = self.llm_client.generate_response(
                prompt, 
                temperature=0.2,  # Low temperature for consistency
                return_json=False
            )
            
            questions = self.parse_response(response, request)
            logger.info(f"Successfully generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            return self._create_fallback_questions(request)
    
    def _create_fallback_questions(self, request: QuestionRequest) -> List[Question]:
        """Create fallback questions when generation fails"""
        questions = []
        for i in range(3):
            questions.append(Question(
                question_number=i + 1,
                question=f"[Generation Error] Question {i + 1} for: {self._get_teaching_point(request)}",
                options=[
                    QuestionOption(key="A", value="Option A"),
                    QuestionOption(key="B", value="Option B")
                ],
                answer=["A"],
                confidence_score=0.0
            ))
        return questions
    
    def _get_teaching_point(self, request: QuestionRequest) -> str:
        """Get teaching point in requested language"""
        return request.teaching_point_en if request.language == Language.ENGLISH else request.teaching_point_ar

class MultipleChoiceGenerator(QuestionGenerator):
    """Specialized generator for multiple choice questions"""
    
    def generate_prompt(self, request: QuestionRequest) -> str:
        teaching_point = self._get_teaching_point(request)
        lang_name = "English" if request.language == Language.ENGLISH else "Arabic"
        
        total_options = request.number_of_distractors + 1
        
        return f"""You are an expert military instructor at the Air Force Defense Institute (AFADI).

TASK: Generate exactly 3 multiple-choice questions testing the {request.bloom_level.value} cognitive level.

TEACHING POINT: {teaching_point}
CONTEXT: {request.context or "Standard AFADI military training context"}
LANGUAGE: {lang_name}
COGNITIVE LEVEL: {request.bloom_level.value}

REQUIREMENTS:
- Each question must have exactly {total_options} options (1 correct, {request.number_of_distractors} distractors)
- Questions must test {request.bloom_level.value} level thinking
- Use realistic military scenarios and terminology
- Avoid obvious answers or patterns
- Make distractors plausible but clearly incorrect

FORMAT (JSON):
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "Question text here",
      "options": [
        {{"key": "A", "value": "First option"}},
        {{"key": "B", "value": "Second option"}},
        {{"key": "C", "value": "Third option"}}
      ],
      "answer": ["A"],
      "confidence_score": 0.95
    }}
  ]
}}
```

Generate exactly 3 questions following this format."""

    def parse_response(self, response: str, request: QuestionRequest) -> List[Question]:
        """Parse JSON response for multiple choice questions"""
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_str = response.strip()
            
            data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(data.get("questions", [])[:3], 1):
                questions.append(Question(
                    question_number=i,
                    question=q_data.get("question", f"Question {i}"),
                    options=[QuestionOption(**opt) for opt in q_data.get("options", [])],
                    answer=q_data.get("answer", ["A"]),
                    confidence_score=q_data.get("confidence_score", 0.8)
                ))
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse multiple choice response: {e}")
            return self._create_fallback_questions(request)

class MultiSelectGenerator(QuestionGenerator):
    """Specialized generator for multi-select questions"""
    
    def generate_prompt(self, request: QuestionRequest) -> str:
        teaching_point = self._get_teaching_point(request)
        lang_name = "English" if request.language == Language.ENGLISH else "Arabic"
        
        total_options = request.number_of_distractors + request.number_of_correct_answers
        
        return f"""You are an expert military instructor at AFADI specializing in complex assessment design.

TASK: Generate exactly 3 multi-select questions requiring analytical thinking.

TEACHING POINT: {teaching_point}
CONTEXT: {request.context or "Standard AFADI operations"}
LANGUAGE: {lang_name}
COGNITIVE LEVEL: {request.bloom_level.value}

REQUIREMENTS:
- Each question must have exactly {total_options} options
- Exactly {request.number_of_correct_answers} options must be correct
- {request.number_of_distractors} options must be incorrect but plausible
- Test complex understanding requiring analysis of multiple factors
- Use realistic military scenarios

FORMAT (JSON):
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "Which factors contribute to effective air defense operations? (Select all that apply)",
      "options": [
        {{"key": "A", "value": "First factor"}},
        {{"key": "B", "value": "Second factor"}},
        {{"key": "C", "value": "Third factor"}},
        {{"key": "D", "value": "Fourth factor"}}
      ],
      "answer": ["A", "C"],
      "confidence_score": 0.90
    }}
  ]
}}
```

Generate exactly 3 questions."""

    def parse_response(self, response: str, request: QuestionRequest) -> List[Question]:
        """Parse JSON response for multi-select questions"""
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(data.get("questions", [])[:3], 1):
                questions.append(Question(
                    question_number=i,
                    question=q_data.get("question", f"Question {i}"),
                    options=[QuestionOption(**opt) for opt in q_data.get("options", [])],
                    answer=q_data.get("answer", ["A", "B"]),
                    confidence_score=q_data.get("confidence_score", 0.8)
                ))
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse multi-select response: {e}")
            return self._create_fallback_questions(request)

class TrueFalseGenerator(QuestionGenerator):
    """Specialized generator for true/false questions"""
    
    def generate_prompt(self, request: QuestionRequest) -> str:
        teaching_point = self._get_teaching_point(request)
        lang_name = "English" if request.language == Language.ENGLISH else "Arabic"
        
        return f"""You are an expert military instructor at AFADI creating precise true/false assessments.

TASK: Generate exactly 3 true/false questions testing critical understanding.

TEACHING POINT: {teaching_point}
CONTEXT: {request.context or "Standard AFADI training"}
LANGUAGE: {lang_name}
COGNITIVE LEVEL: {request.bloom_level.value}

REQUIREMENTS:
- Create definitive statements that are clearly true or false
- Avoid ambiguous wording
- Test important concepts, not trivial details
- Include common misconceptions as false statements
- Balance true and false answers across the 3 questions

FORMAT (JSON):
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "In air defense operations, early warning systems must always be positioned at the highest available elevation.",
      "options": [
        {{"key": "A", "value": "True"}},
        {{"key": "B", "value": "False"}}
      ],
      "answer": ["B"],
      "confidence_score": 0.95
    }}
  ]
}}
```

Generate exactly 3 questions."""

    def parse_response(self, response: str, request: QuestionRequest) -> List[Question]:
        """Parse JSON response for true/false questions"""
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(data.get("questions", [])[:3], 1):
                questions.append(Question(
                    question_number=i,
                    question=q_data.get("question", f"Question {i}"),
                    options=[
                        QuestionOption(key="A", value="True"),
                        QuestionOption(key="B", value="False")
                    ],
                    answer=q_data.get("answer", ["A"]),
                    confidence_score=q_data.get("confidence_score", 0.8)
                ))
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse true/false response: {e}")
            return self._create_fallback_questions(request)

class TrueFalseJustificationGenerator(QuestionGenerator):
    """Specialized generator for true/false with justification"""
    
    def generate_prompt(self, request: QuestionRequest) -> str:
        teaching_point = self._get_teaching_point(request)
        lang_name = "English" if request.language == Language.ENGLISH else "Arabic"
        
        return f"""You are an expert military instructor at AFADI creating advanced true/false assessments with justifications.

TASK: Generate exactly 3 true/false questions with detailed explanations.

TEACHING POINT: {teaching_point}
CONTEXT: {request.context or "Standard AFADI training"}
LANGUAGE: {lang_name}
COGNITIVE LEVEL: {request.bloom_level.value}

REQUIREMENTS:
- Create complex statements requiring deep understanding
- Provide comprehensive justifications explaining the reasoning
- Include references to military doctrine where applicable
- Explanations should be educational and detailed
- Balance true and false answers

FORMAT (JSON):
```json
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "Air defense systems are most effective when operated in complete isolation from other military units.",
      "options": [
        {{"key": "A", "value": "True"}},
        {{"key": "B", "value": "False"}}
      ],
      "answer": ["B"],
      "model_answer": "False. Air defense systems are most effective when integrated with other military units through coordinated command and control systems. Integration allows for shared intelligence, mutual support, and comprehensive battlefield awareness. Isolated operations limit situational awareness and reduce overall defensive effectiveness.",
      "confidence_score": 0.95
    }}
  ]
}}
```

Generate exactly 3 questions."""

    def parse_response(self, response: str, request: QuestionRequest) -> List[Question]:
        """Parse JSON response for true/false with justification"""
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response.strip()
            
            data = json.loads(json_str)
            questions = []
            
            for i, q_data in enumerate(data.get("questions", [])[:3], 1):
                questions.append(Question(
                    question_number=i,
                    question=q_data.get("question", f"Question {i}"),
                    options=[
                        QuestionOption(key="A", value="True"),
                        QuestionOption(key="B", value="False")
                    ],
                    answer=q_data.get("answer", ["A"]),
                    model_answer=q_data.get("model_answer", "Justification not provided"),
                    confidence_score=q_data.get("confidence_score", 0.8)
                ))
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse true/false justification response: {e}")
            return self._create_fallback_questions(request)
