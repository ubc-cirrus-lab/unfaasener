import json
import base64
import json
from datetime import datetime
import uuid

def lambda_handler(event, context):
    
    if event:
        videoName = event['videoName']
        fanoutNum = event['fanoutNum']
        reqID = uuid.uuid4().hex
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'videoName': videoName, 'reqID': reqID, 'fanoutNum': fanoutNum},
        })
    }
