import json
import datetime
import uuid

def lambda_handler(event, context):
    
    n_samples = int (event['n_samples'])
    reqID = uuid.uuid4().hex
    
    return {
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'reqID':reqID },
        })
    }