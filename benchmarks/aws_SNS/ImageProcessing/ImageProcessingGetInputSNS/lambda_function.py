import json
import datetime
import uuid
import boto3

def lambda_handler(event, context):
    try:
        imageName = event['input_image']
    except:
        print("The input should contain the name of the input image")
    
    reqID = uuid.uuid4().hex
    
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': imageName, 'reqID': reqID},
        })
    })
    
    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:ImageProcessingFlip",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }