import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    
    # Get input
    print("Text2speech Raw Function")
    print(event)
    print(json.loads(event['body']))
    input = json.loads(event['body'])['data']['input']
    #bucket = s3.Bucket('text2speechbenchmark')
    
    client = boto3.client('polly')
    polly_response = client.start_speech_synthesis_task(
        OutputFormat='mp3',
        OutputS3BucketName='text2speech-polly',
        Text=input,
        VoiceId='Joanna'
    )
    
    task_id=polly_response['SynthesisTask']['TaskId']
    object_url=polly_response['SynthesisTask']['OutputUri']
    object_data={'TaskId':task_id,'OutputUri':object_url}
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'input': input, 'result': object_data},
        })
    }
