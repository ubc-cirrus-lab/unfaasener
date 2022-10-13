import json
import datetime
import uuid
import logging

def getInput(request):

    request_json = request.get_json()
    print(f'request json is {request_json}')
    imageName = request_json['message']

    reqID = uuid.uuid4().hex

    print(f'reqId is {reqID} and imageName is {imageName}')

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'imageName': imageName, 'reqID': reqID},
        }
    })
