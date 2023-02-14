import json
import boto3
import botocore
from datetime import datetime

s3 = boto3.resource('s3')
bucket = s3.Bucket("regression-tuning-storage")
            
def lambda_handler(event, context):
    print(f"Event is {event}")
    
    if event == {}:
        print("Error: Event is not provided")
        return
    else:
        msg = event['Records'][0]['Sns']['Message']
        body = (json.loads(msg))['body']
        data = (json.loads(body))['data']

        n_samples = data['n_samples']
        req_id = data['reqID']
        
        # If merge is invoked from the first model, do nothing
        if "firstModel" in data:
            return {'statusCode': 200}
        # If merge is invoked from the second model, publish the notification for join runs 
        else:
            second_model = data['secondModel']
            # check if first model exists in the bucket 
            first_model = req_id + '-model1.tar.gz'
            response = {}
            while True:
                try:
                    s3.Object('regression-tuning-storage', first_model).load()
                    
                    print(f"Sending the notification to JoinRuns")
                    notification = json.dumps({
                        'statusCode': 200,
                        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                        'body': json.dumps({
                            'data': {'n_samples': n_samples, 'firstModel': first_model, 'secondModel':second_model, 'reqID': req_id}
                        })
                    })
                    
                    client = boto3.client('sns')
    
                    response = client.publish (
                      TargetArn = "arn:aws:sns:us-east-2:417140135939:RegressionTuningJoinRuns",
                      Message = json.dumps({'default': notification}),
                      MessageStructure = 'json'
                    )
                    break
                except botocore.exceptions.ClientError as e:
                    # File does not exist yet
                    continue
        
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }