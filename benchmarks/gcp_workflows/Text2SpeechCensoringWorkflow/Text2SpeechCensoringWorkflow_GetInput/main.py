import base64
import json
from datetime import datetime
import logging
import uuid
from sys import getsizeof
import random

def get(request):
    reqID = uuid.uuid4().hex
    request_json = request.get_json()
    message = "Hello World"
    if request.args and 'message' in request.args:
        message =  request.args.get('message')
    elif request_json and 'message' in request_json:
        message =  request_json['message']

    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message': message, 'reqID': reqID},
        }
      }