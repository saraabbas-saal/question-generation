import pandas as pd
import requests
import random as rand


API_URL= 'http://192.168.71.70:8888/generate-questions'


def read_test_set():
    df= pd.read_csv('./data/teaching_points_examples.csv')
    # print(df)

    return df

def append_request(data):
    data['language']= rand.choice(['en','ar'])
    data['question_type']= rand.choice(["MULTICHOICE", "MULTI_SELECT", "TRUE_FALSE", "TRUE_FALSE_JUSTIFICATION"])
    data['number_of_distractors']= rand.randrange(1,6)
    if data['question_type']== "MULTI_SELECT":
        data['number_of_correct_answers']=  rand.randrange(2,7)
    data['bloom_level']= rand.choice(['REMEMBER', 'UNDERSTAND',  'APPLY', 'ANALYSE', 'EVALUATE', 'CREATE'])

    return data


def call_endpoint_all_records(API_URL):

    df_test= read_test_set()
    df_responses= pd.DataFrame()
    all_rows = []

    for _,row in df_test.iterrows():
        data= row.to_dict()
        data= append_request(data)
        response= requests.post(API_URL, json= data )
        # print(response.text)
        # print("????????????????????????????????")
        # df_responses.concat(response)

    # return df_responses

    


if __name__=='__main__':
    # read_test_set()
    data= call_endpoint_all_records(API_URL)
    print(data)
    
    # append_request(data)
    # print(data)