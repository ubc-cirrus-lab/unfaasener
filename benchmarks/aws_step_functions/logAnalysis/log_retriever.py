import boto3
import re
import json
import time 
import datetime
import pandas as pd
import os
import uuid

def lambda_handler(event, context):
    function_name = event['function_name']
    
    path = "/aws/lambda/" + function_name
    client = boto3.client("logs")
    
    stream_response = client.describe_log_streams(
        logGroupName="/aws/lambda/" + function_name,
        orderBy='LastEventTime',                 
        descending=True
        )
        
    logStreamNames = []
    for s in  stream_response["logStreams"]:
        logStreamNames.append(s["logStreamName"])
        
    response = []
    for n in logStreamNames:
        response.append(client.get_log_events(
        logGroupName="/aws/lambda/" + function_name,
        logStreamName=n)["events"][-1])
        
    df = pd.DataFrame (response, columns = ['timestamp', 'message', 'ingestionTime'])
    df['message'] = df['message'].str.replace('REPORT ', '')
    df['message'] = df['message'].str.replace('\n', '')
    df['message'] = df['message'].str.replace(' ', '')
    
    df[['RequestId','Duration', 'Billed Duration', 'Memory Size', 'Max Memory Used', 'Init Duration', 'XRAY TraceId', 'SegmentId', 'Sampled', 'col']] = df.message.str.split('\t', expand=True)
    print(df['Init Duration'])
    df['RequestId'] = df['RequestId'].str.replace('RequestId:', '')
    
    df['Duration'] = df['Duration'].str.replace('Duration:', '')
    df['Duration'] = df['Duration'].str.replace('ms', '')
    df['Duration'] = df['Duration'].astype('float')

    df['Billed Duration'] = df['Billed Duration'].str.replace('BilledDuration:', '')
    df['Billed Duration'] = df['Billed Duration'].str.replace('ms', '')
    df['Billed Duration'] = df['Billed Duration'].astype('int')
    
    df['Memory Size'] = df['Memory Size'].str.replace('MemorySize:', '')
    df['Memory Size'] = df['Memory Size'].str.replace('MB', '')
    df['Memory Size'] = df['Memory Size'].astype('int')
    
    df['Max Memory Used'] = df['Max Memory Used'].str.replace('MaxMemoryUsed:', '')
    df['Max Memory Used'] = df['Max Memory Used'].str.replace('MB', '')
    df['Max Memory Used'] = df['Max Memory Used'].astype('int')
    
    df['Init Duration'] = df['Init Duration'].str.replace('InitDuration:', '')
    df['Init Duration'] = df['Init Duration'].str.replace('ms', '')
    df['Init Duration'] = df['Init Duration'].astype('float')
    
    id = uuid.uuid4().hex
    path = f'/tmp/log_data_{id}.csv'
    df.to_csv(path, index=False)
    s3 = boto3.resource('s3')
    bucket = s3.Bucket("benchmarklogs")
    bucket.upload_file(path, f'log_data_{id}.csv')
    os.remove(path)
    
    return response