import json
import datetime
import uuid
import boto3

def lambda_handler(event, context):
    
    # This is for running power tuning
    if event == {}:
        n_samples = 10
    else:
        n_samples = int (event['n_samples'])
    
    # Creating a request ID for this invocation   
    reqID = uuid.uuid4().hex
    
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'reqID':reqID },
        })
    })
    
    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:RegressionTuningCreateDataset",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }