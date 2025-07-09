import pandas as pd
import requests
import random as rand
import json
from typing import List, Dict, Any
import time


API_URL = 'http://192.168.71.70:8888/generate-questions'


def read_test_set():
    """Read the teaching points CSV file"""
    df = pd.read_csv('./data/teaching_points_examples.csv')
    return df


def append_request(data):
    """Add random parameters to the request data"""
    data['language'] = rand.choice(['en', 'ar'])
    data['question_type'] = rand.choice(["MULTICHOICE", "MULTI_SELECT", "TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"])
    
    # Fix: Ensure minimum 2 distractors as per your API validation
    data['number_of_distractors'] = rand.randrange(2, 6)  # Changed from 1,6 to 2,6
    
    if data['question_type'] == "MULTI_SELECT":
        # Ensure number of correct answers is reasonable
        max_correct = min(4, data['number_of_distractors'] - 1)  # Don't exceed total options
        data['number_of_correct_answers'] = rand.randrange(1, max_correct + 1)
    
    data['bloom_level'] = rand.choice(['REMEMBER', 'UNDERSTAND', 'APPLY', 'ANALYZE', 'EVALUATE', 'CREATE'])  # Fixed 'ANALYSE' to 'ANALYZE'
    
    return data


def parse_response_to_dataframe_rows(response_json: dict, request_data: dict) -> List[Dict]:
    """
    Parse API response JSON into DataFrame rows
    
    Args:
        response_json: The JSON response from the API
        request_data: The original request data for context
        
    Returns:
        List of dictionaries representing DataFrame rows
    """
    rows = []
    
    if 'questions' not in response_json:
        # Handle error responses
        print(f"Error in response: {response_json}")
        return rows
    
    # Extract metadata from response
    metadata = {
        'teaching_point': response_json.get('teaching_point', ''),
        'question_type': response_json.get('question_type', ''),
        'language': response_json.get('language', ''),
        'bloom_level': response_json.get('bloom_level', ''),
        'request_language': request_data.get('language', ''),
        'request_question_type': request_data.get('question_type', ''),
        'request_bloom_level': request_data.get('bloom_level', ''),
        'number_of_distractors': request_data.get('number_of_distractors', 0),
        'number_of_correct_answers': request_data.get('number_of_correct_answers', 0),
        'teaching_point_en': request_data.get('teaching_point_en', ''),
        'teaching_point_ar': request_data.get('teaching_point_ar', ''),
    }
    
    # Process each question
    for question in response_json['questions']:
        row = metadata.copy()  # Start with metadata
        
        # Add question-specific data
        row.update({
            'question_number': question.get('question_number', 0),
            'question_text': question.get('question', ''),
            'model_answer': question.get('model_answer', ''),
            'num_options': len(question.get('options', [])),
            'correct_answers': ', '.join(question.get('answer', [])),
            'num_correct_answers': len(question.get('answer', [])),
        })
        
        # Add individual options (up to 6)
        options = question.get('options', [])
        for i, option_key in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
            option_value = ''
            for opt in options:
                if opt.get('key', '').upper() == option_key:
                    option_value = opt.get('value', '')
                    break
            row[f'option_{option_key}'] = option_value
        
        # Add formatted options string
        options_text = []
        for opt in options:
            key = opt.get('key', '')
            value = opt.get('value', '')
            if key and value:
                options_text.append(f"{key}) {value}")
        row['options_formatted'] = ' | '.join(options_text)
        
        rows.append(row)
    
    return rows


def call_endpoint_all_records(API_URL):
    """
    Call the API for all records and store responses in DataFrame
    
    Args:
        API_URL: The API endpoint URL
        
    Returns:
        pandas.DataFrame: DataFrame containing all responses
    """
    df_test = read_test_set()
    all_rows = []
    
    print(f"Processing {len(df_test)} test records...")
    
    for idx, row in df_test.iterrows():
        try:
            print(f"Processing record {idx + 1}/{len(df_test)}")
            
            # Prepare request data
            data = row.to_dict()
            data = append_request(data)
            
            print(f"  Request: {data['question_type']} | {data['language']} | {data['bloom_level']}")
            
            # Make API call
            response = requests.post(API_URL, json=data, timeout=30)
            
            if response.status_code == 200:
                response_json = response.json()
                
                # Parse response into DataFrame rows
                rows = parse_response_to_dataframe_rows(response_json, data)
                all_rows.extend(rows)
                
                print(f"  Success: Added {len(rows)} questions")
                
            else:
                print(f"  Error {response.status_code}: {response.text}")
                
                # Add error record
                error_row = {
                    'teaching_point_en': data.get('teaching_point_en', ''),
                    'teaching_point_ar': data.get('teaching_point_ar', ''),
                    'request_question_type': data.get('question_type', ''),
                    'request_language': data.get('language', ''),
                    'request_bloom_level': data.get('bloom_level', ''),
                    'error_status': response.status_code,
                    'error_message': response.text[:500],  # Truncate long error messages
                    'question_number': 0,
                    'question_text': 'ERROR_RESPONSE',
                }
                all_rows.append(error_row)
            
            # Small delay to be nice to the API
            time.sleep(0.5)
            
        except requests.exceptions.Timeout:
            print(f"  Timeout error for record {idx + 1}")
            error_row = {
                'teaching_point_en': row.get('teaching_point_en', ''),
                'error_message': 'Request timeout',
                'question_text': 'TIMEOUT_ERROR',
            }
            all_rows.append(error_row)
            
        except requests.exceptions.RequestException as e:
            print(f"  Request error for record {idx + 1}: {e}")
            error_row = {
                'teaching_point_en': row.get('teaching_point_en', ''),
                'error_message': str(e),
                'question_text': 'REQUEST_ERROR',
            }
            all_rows.append(error_row)
            
        except Exception as e:
            print(f"  Unexpected error for record {idx + 1}: {e}")
            error_row = {
                'teaching_point_en': row.get('teaching_point_en', ''),
                'error_message': str(e),
                'question_text': 'UNKNOWN_ERROR',
            }
            all_rows.append(error_row)
    
    # Create DataFrame from all collected rows
    if all_rows:
        df_responses = pd.DataFrame(all_rows)
        print(f"\nCompleted! Created DataFrame with {len(df_responses)} total rows")
        print(f"Successful questions: {len(df_responses[df_responses['question_text'] != 'ERROR_RESPONSE'])}")
        print(f"Errors: {len(df_responses[df_responses['question_text'] == 'ERROR_RESPONSE'])}")
        return df_responses
    else:
        print("\nNo data collected!")
        return pd.DataFrame()

def save_results(df_responses: pd.DataFrame, filename: str = 'afadi_question_gen_responses.csv'):
    """Save the results to CSV"""
    if df_responses.empty:
        print("No data to save")
        return
    
    df_responses.to_csv(filename, index=False)
    print(f"Results saved to {filename}")

def analyze_results(df_responses: pd.DataFrame):
    """Print analysis of the results"""
    if df_responses.empty:
        print("No data to analyze")
        return
    
    print("\n=== RESULTS ANALYSIS ===")
    print(f"Total rows: {len(df_responses)}")
    
    if 'question_text' in df_responses.columns:
        successful = df_responses[~df_responses['question_text'].str.contains('ERROR|TIMEOUT', na=False)]
        errors = df_responses[df_responses['question_text'].str.contains('ERROR|TIMEOUT', na=False)]
        
        print(f"Successful questions: {len(successful)}")
        print(f"Errors: {len(errors)}")
    
    if 'request_question_type' in df_responses.columns:
        print(f"\nQuestion types:")
        print(df_responses['request_question_type'].value_counts())
    
    if 'request_language' in df_responses.columns:
        print(f"\nLanguages:")
        print(df_responses['request_language'].value_counts())


if __name__ == '__main__':
    # Call the API for all records
    df_responses = call_endpoint_all_records(API_URL)
    
    # Analyze results
    analyze_results(df_responses)
    
    # Save results
    save_results(df_responses)
    
    # Display sample
    if not df_responses.empty:
        print("\n=== SAMPLE DATA ===")
        columns_to_show = ['question_type', 'question_number', 'question_text', 'correct_answers']
        available_columns = [col for col in columns_to_show if col in df_responses.columns]
        if available_columns:
            print(df_responses[available_columns].head(10))