import json
import datetime
import uuid

def lambda_handler(event, context):
    
    if event == {}:
        imageName = 'sample_2.png'
        reqID = uuid.uuid4().hex
    else:
        imageName = event['input_image']
        reqID = uuid.uuid4().hex
    
    return {
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': imageName, 'reqID': reqID},
        })
    }