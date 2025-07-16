// Question generation data models
class QuestionOption {
  key string
  value string
}

class GeneratedQuestion {
  question_number int
  question string
  options QuestionOption[]
  answer string[]
  explanation string?  // Changed from model_answer to explanation
}

class QuestionGenerationResult {
  
  questions GeneratedQuestion[]
  teaching_point string
  question_type string
  language string
  bloom_level string
}

// Function to generate questions based on teaching points
function GenerateQuestions(
  teaching_point_en: string,
  teaching_point_ar: string,
  context: string?,
  question_type: string,
  number_of_distractors: int?,
  number_of_correct_answers: int?,
  language: string,
  bloom_level: string
) -> QuestionGenerationResult {
  client "VLLM"
  prompt #"
    You are an expert military instructor generating questions for your students. Generate exactly 3 questions based on the teaching point provided.


    **Teaching Point (English):** {{ teaching_point_en }}
    **Teaching Point (Arabic):** {{ teaching_point_ar }}
    {% if context %}**Additional Context:** {{ context }}{% endif %}
    
    **Question Type:** {{ question_type }}
    **Language:** {{ language }} (use "en" for English, "ar" for Arabic)
    **Bloom's Taxonomy Level:** {{ bloom_level }}
    {% if number_of_distractors %}**Number of Distractors:** {{ number_of_distractors }}{% endif %}
    {% if number_of_correct_answers %}**Number of Correct Answers:** {{ number_of_correct_answers }}{% endif %}


    **Bloom's Taxonomy Guidelines:**
    - REMEMBER: Recall facts, basic concepts, answers
    - UNDERSTAND: Explain ideas, concepts, summarize
    - APPLY: Use information in new situations
    - ANALYZE: Draw connections, examine and break down
    - EVALUATE: Justify decisions or opinions
    - CREATE: Produce new or original work
    
    **INSTRUCTIONS:**
    1. Generate exactly 3 questions that test the teaching point at the {{ bloom_level }} level
    2. Questions should be in {{ language }} language (English if "en", Arabic if "ar")
    3. Use the appropriate teaching point (English or Arabic) based on the language
    
    **Question Type Specific Rules:**
    
    {% if question_type == "MULTICHOICE" %}
    - Create multiple choice questions with {{ number_of_distractors | default(3) }} distractors + 1 correct answer
    - Use options A, B, C, D (or more if needed)
    - Answer format: ["A"] (single correct answer)
    - explanation should be null
    {% elif question_type == "MULTI_SELECT" %}
    - Create multiple select questions with {{ number_of_distractors | default(3) }} distractors + {{ number_of_correct_answers | default(2) }} correct answers
    - Use options A, B, C, D (or more if needed)
    - Answer format: ["A", "C"] (multiple correct answers)
    - explanation should be null
    {% elif question_type == "TRUE_FALSE" %}
    - Create true/false questions
    - Use options: A="True", B="False"
    - Answer format: ["A"] or ["B"]
    - explanation should be null
    {% elif question_type == "TRUE_FALSE_JUSTIFICATION" %}
    - Create true/false questions with justification
    - Use options: A="True", B="False"
    - Answer format: ["A"] or ["B"]
    - explanation should contain a detailed explanation/justification
    {% endif %}

    **Output Requirements:**
    - Always return exactly 3 questions
    - Question numbers: 1, 2, 3
    - Options format: [{"key": "A", "value": "option text"}, {"key": "B", "value": "option text"}]
    - Language in response should be "english" or "arabic" (not "en"/"ar")
    - teaching_point should be the English version
    - Ensure questions are educational, relevant, and appropriately challenging

    {{ ctx.output_format }}
  "#
}

// Test cases for different question types

test multichoice_english {
  functions [GenerateQuestions]
  args {
    teaching_point_en "Explain the AFADI LTEM Environment framework element (VUCAR)"
    teaching_point_ar "يشرح عناصر إطار عمل نموذج تدريب وتعليم القيادة في معهد القوات الجوية والدفاع الجوي"
    context ""
    question_type "MULTICHOICE"
    number_of_distractors 3
    number_of_correct_answers null
    language "en"
    bloom_level "UNDERSTAND"
  }
}

test multiselect_english {
  functions [GenerateQuestions]
  args {
    teaching_point_en "Identify key leadership principles in military operations"
    teaching_point_ar "تحديد المبادئ الرئيسية للقيادة في العمليات العسكرية"
    context "Focus on tactical decision-making scenarios"
    question_type "MULTI_SELECT"
    number_of_distractors 2
    number_of_correct_answers 2
    language "en"
    bloom_level "APPLY"
  }
}

test true_false_arabic {
  functions [GenerateQuestions]
  args {
    teaching_point_en "Understand communication protocols in air defense"
    teaching_point_ar "فهم بروتوكولات الاتصال في الدفاع الجوي"
    context null
    question_type "TRUE_FALSE"
    number_of_distractors null
    number_of_correct_answers null
    language "ar"
    bloom_level "REMEMBER"
  }
}

test true_false_justification_english {
  functions [GenerateQuestions]
  args {
    teaching_point_en "Evaluate the effectiveness of air defense systems"
    teaching_point_ar "تقييم فعالية أنظمة الدفاع الجوي"
    context "Consider both technological and human factors"
    question_type "TRUE_FALSE_JUSTIFICATION"
    number_of_distractors null
    number_of_correct_answers null
    language "en"
    bloom_level "EVALUATE"
  }
}

test arabic_multichoice {
  functions [GenerateQuestions]
  args {
    teaching_point_en "Analyze tactical advantages of air defense positioning"
    teaching_point_ar "تحليل الميزات التكتيكية لتموضع الدفاع الجوي"
    context "في البيئات الحضرية والصحراوية"
    question_type "MULTICHOICE"
    number_of_distractors 3
    number_of_correct_answers null
    language "ar"
    bloom_level "ANALYZE"
  }
}