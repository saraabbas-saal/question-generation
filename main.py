from fastapi import FastAPI, Request
from pydantic import BaseModel
from app.llm_utils import get_llm_response

app = FastAPI()

class Query(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_text(query: Query):
    response = get_llm_response(query.prompt)
    return {"response": response}


def set_map_prompt(teaching_point, question_type, discriminator, lang, question_n=3):
    """
    Creates a prompt template for question generation
    Args:
        lang (str): Language identifier (e.g., "english", "arabic")
    
    Returns:
        str: A prompt template for question generation based on a teaching point
    """
    map_prompt_template = f"""
    You are a smart instructor designed to generate assessment questions for the military Air Force Defense and Institute (AFADI).
     You will be given a teaching point in {lang} language, which is linked to a specific military concept or learning objective. 
     Your task is to: 
     - Understand the semantic meaning of the teaching point. 
     - Apply Bloom’s Taxonomy to determine appropriate cognitive levels (e.g., understand, apply, analyze). 
     - Generate {question_n} {question_type} questions: 
     
     Five Multiple Choice Question (MCQ) 
     Guidelines: AFADI refers to the Air Force Defense and Institute — always maintain relevance to this context. 
     - Avoid simply rephrasing the teaching point. Be creative and focus on implications, applications, comparisons, and conceptual understanding. 
     - Use military air defense scenarios or terminology where appropriate. Ensure all questions are clear, relevant, and test different levels of cognitive ability.
     -  
     Teaching Point: {teaching_point}
    ```{{text}}```
    FULL SUMMARY:
    """

    return map_prompt_template


if __name__ == "__main__":
   
    # Run with uvicorn with optimized settings
    uvicorn.run(
        app, 
        port=8000,
        workers=4,
        log_level="info"
    )