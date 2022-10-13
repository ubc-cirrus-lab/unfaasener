import json
import base64
import json
from datetime import datetime
import uuid

def get(request):

    request_json = request.get_json()
    print(request_json)
    videoName = request_json['videoName']
    fanoutNum = request_json['fanoutNum']

    reqID = uuid.uuid4().hex

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'videoName': videoName, 'reqID': reqID, 'fanoutNum': fanoutNum}
        }
    })