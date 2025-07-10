#!/usr/bin/env python3
"""
OpenAI Military Question Analyzer
Analyzes military training questions and generates correct answers using OpenAI API
"""

import pandas as pd
import openai
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime
import os
from tqdm import tqdm
from config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('military_question_analysis.log'),
        logging.StreamHandler()
    ]
)

class MilitaryQuestionAnalyzer:
    """
    Analyzes military training questions using OpenAI API and generates correct answers
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", max_retries: int = 3):
        """
        Initialize the analyzer
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: gpt-4)
            max_retries: Maximum number of retries for API calls
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        
        # Military expert system prompt
        self.system_prompt = """
        You are a highly experienced military instructor and expert in Air Force Defense operations, 
        specializing in military doctrine, leadership, human factors, and operational procedures.
        
        Your expertise includes:
        - Military leadership and management principles
        - Air defense operations and tactics
        - Human factors in military operations
        - Emotional intelligence in military contexts
        - Military training and development
        - Operational psychology and decision-making
        - Military communication and team dynamics
        - Self-assessment and personal development in military context
        
        When analyzing questions, consider:
        1. Standard military doctrine and principles
        2. Air Force specific procedures and knowledge
        3. Leadership responsibilities and ethics
        4. Human factors and psychological principles
        5. Operational effectiveness and safety
        6. Military hierarchy and command structure
        7. Cultural sensitivity in military contexts
        
        Provide accurate, doctrine-based answers that reflect current military best practices.
        """
    
    def analyze_question(self, question_data: Dict) -> Dict:
        """
        Analyze a single question using OpenAI API
        
        Args:
            question_data: Dictionary containing question information
            
        Returns:
            Dictionary with analysis results
        """
        
        # Extract question components
        teaching_point = question_data.get('teaching_point', '')
        question_text = question_data.get('question_text', '')
        options = question_data.get('options_formatted', '')
        given_answer = question_data.get('correct_answers', '')
        
        # Create analysis prompt
        analysis_prompt = f"""
        Analyze this military training question and provide the correct answer:

        **Teaching Point:** {teaching_point}
        
        **Question:** {question_text}
        
        **Options:** {options}
        
        **Given Answer:** {given_answer}
        
        Please provide your analysis in the following JSON format:
        {{
            "correct_answer": "The correct answer (A, B, C, D, [A,B], etc.)",
            "confidence_level": "HIGH/MEDIUM/LOW",
            "verification_status": "CORRECT/INCORRECT/NEEDS_REVIEW",
            "explanation": "Brief explanation of why this is the correct answer based on military doctrine",
            "key_principle": "The main military principle or concept this question tests"
        }}
        
        Consider:
        - Military doctrine and standard operating procedures
        - Leadership principles and responsibilities
        - Human factors and operational psychology
        - Air defense specific knowledge
        - Safety and effectiveness considerations
        - Cultural and linguistic context (for Arabic questions)
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent analysis
                    max_tokens=500
                )
                
                # Parse the response
                content = response.choices[0].message.content
                
                # Try to extract JSON from the response
                try:
                    # Look for JSON block in the response
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        analysis_result = json.loads(json_match.group(1))
                    else:
                        # Try to find JSON without code blocks
                        json_match = re.search(r'(\{.*?\})', content, re.DOTALL)
                        if json_match:
                            analysis_result = json.loads(json_match.group(1))
                        else:
                            raise ValueError("No valid JSON found in response")
                    
                    # Validate required fields
                    required_fields = ['correct_answer', 'confidence_level', 'verification_status', 'explanation']
                    if not all(field in analysis_result for field in required_fields):
                        raise ValueError("Missing required fields in analysis result")
                    
                    # Add metadata
                    analysis_result['api_model'] = self.model
                    analysis_result['analysis_timestamp'] = datetime.now().isoformat()
                    
                    return analysis_result
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logging.warning(f"Failed to parse JSON response on attempt {attempt + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        return {
                            'correct_answer': given_answer,
                            'confidence_level': 'LOW',
                            'verification_status': 'NEEDS_REVIEW',
                            'explanation': f'Failed to parse API response: {content[:100]}...',
                            'key_principle': 'Unknown',
                            'api_model': self.model,
                            'analysis_timestamp': datetime.now().isoformat()
                        }
                
            except Exception as e:
                logging.error(f"API call failed on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        'correct_answer': given_answer,
                        'confidence_level': 'LOW',
                        'verification_status': 'ERROR',
                        'explanation': f'API call failed: {str(e)}',
                        'key_principle': 'Unknown',
                        'api_model': self.model,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                
                # Wait before retry
                time.sleep(2 ** attempt)
        
        return None
    
    def analyze_csv(self, input_file: str, output_file: str = None) -> pd.DataFrame:
        """
        Analyze all questions in a CSV file
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            
        Returns:
            DataFrame with analysis results
        """
        
        logging.info(f"Starting analysis of {input_file}")
        
        # Read CSV file
        try:
            df = pd.read_csv(input_file, sep='\t' if input_file.endswith('.txt') else ',')
            logging.info(f"Loaded {len(df)} questions from {input_file}")
        except Exception as e:
            logging.error(f"Failed to read CSV file: {e}")
            raise
        
        # Initialize result columns
        df['openai_correct_answer'] = ''
        df['openai_confidence_level'] = ''
        df['openai_verification_status'] = ''
        df['openai_explanation'] = ''
        df['openai_key_principle'] = ''
        df['openai_model'] = ''
        df['openai_analysis_timestamp'] = ''
        
        # Analyze each question
        successful_analyses = 0
        failed_analyses = 0
        
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Analyzing questions"):
            try:
                # Convert row to dictionary
                question_data = row.to_dict()
                
                # Analyze the question
                analysis_result = self.analyze_question(question_data)
                
                if analysis_result:
                    # Update DataFrame with results
                    df.loc[index, 'openai_correct_answer'] = analysis_result.get('correct_answer', '')
                    df.loc[index, 'openai_confidence_level'] = analysis_result.get('confidence_level', '')
                    df.loc[index, 'openai_verification_status'] = analysis_result.get('verification_status', '')
                    df.loc[index, 'openai_explanation'] = analysis_result.get('explanation', '')
                    df.loc[index, 'openai_key_principle'] = analysis_result.get('key_principle', '')
                    df.loc[index, 'openai_model'] = analysis_result.get('api_model', '')
                    df.loc[index, 'openai_analysis_timestamp'] = analysis_result.get('analysis_timestamp', '')
                    
                    successful_analyses += 1
                    logging.info(f"Analyzed question {index + 1}: {analysis_result.get('verification_status', 'Unknown')}")
                else:
                    failed_analyses += 1
                    logging.error(f"Failed to analyze question {index + 1}")
                
                # Rate limiting - wait between requests
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Error analyzing question {index + 1}: {e}")
                failed_analyses += 1
                continue
        
        # Generate summary statistics
        self.generate_summary_report(df, successful_analyses, failed_analyses)
        
        # Save results
        if output_file:
            df.to_csv(output_file, index=False)
            logging.info(f"Results saved to {output_file}")
        
        return df
    
    def generate_summary_report(self, df: pd.DataFrame, successful: int, failed: int):
        """
        Generate a summary report of the analysis
        
        Args:
            df: DataFrame with analysis results
            successful: Number of successful analyses
            failed: Number of failed analyses
        """
        
        total_questions = len(df)
        
        # Count verification statuses
        status_counts = df['openai_verification_status'].value_counts()
        
        # Count confidence levels
        confidence_counts = df['openai_confidence_level'].value_counts()
        
        # Generate report
        report = f"""
        
        ========================================
        MILITARY QUESTION ANALYSIS REPORT
        ========================================
        
        Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Model Used: {self.model}
        
        PROCESSING SUMMARY:
        - Total Questions: {total_questions}
        - Successfully Analyzed: {successful}
        - Failed Analyses: {failed}
        - Success Rate: {(successful/total_questions)*100:.1f}%
        
        VERIFICATION STATUS BREAKDOWN:
        {status_counts.to_string() if not status_counts.empty else 'No data'}
        
        CONFIDENCE LEVEL BREAKDOWN:
        {confidence_counts.to_string() if not confidence_counts.empty else 'No data'}
        
        CORRECTNESS ANALYSIS:
        """
        
        # Compare with given answers
        if 'correct_answers' in df.columns:
            matches = (df['openai_correct_answer'] == df['correct_answers']).sum()
            report += f"- Matches with given answers: {matches}/{total_questions} ({(matches/total_questions)*100:.1f}%)\n"
        
        logging.info(report)
        
        # Save report to file
        with open(f'military_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w') as f:
            f.write(report)

def main():
    """
    Main function to run the analysis
    """
    
    # Configuration
    API_KEY = os.getenv('OPENAI_API_KEY')  # Set your API key as environment variable
    INPUT_FILE = 'afadi_question_generation_testing.csv'  # Your input file
    OUTPUT_FILE = f'military_questions_analyzed_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    MODEL = 'gpt-4'  # Use gpt-4 for best results, or gpt-3.5-turbo for faster/cheaper analysis
    
    if not API_KEY:
        print("Error: Please set your OpenAI API key as environment variable OPENAI_API_KEY")
        print("Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize analyzer
    analyzer = MilitaryQuestionAnalyzer(
        api_key=API_KEY,
        model=MODEL,
        max_retries=3
    )
    
    try:
        # Run analysis
        results_df = analyzer.analyze_csv(INPUT_FILE, OUTPUT_FILE)
        
        print(f"\n✅ Analysis complete!")
        print(f"📊 Results saved to: {OUTPUT_FILE}")
        print(f"📋 Check the log file: military_question_analysis.log")
        print(f"📈 Summary report saved with timestamp")
        
        # Display quick summary
        print(f"\n📋 Quick Summary:")
        print(f"Total questions analyzed: {len(results_df)}")
        if 'openai_verification_status' in results_df.columns:
            status_counts = results_df['openai_verification_status'].value_counts()
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()