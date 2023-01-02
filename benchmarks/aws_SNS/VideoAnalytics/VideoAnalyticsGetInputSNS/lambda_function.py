import json
import base64
import json
from datetime import datetime
import uuid
import boto3

def lambda_handler(event, context):
    
    if event:
        videoName = event['videoName']
        fanoutNum = event['fanoutNum']
        reqID = uuid.uuid4().hex
    
    # Return
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'videoName': videoName, 'reqID': reqID, 'fanoutNum': fanoutNum},
        })
    })
    
    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:VideoAnalytics_Streaming",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }