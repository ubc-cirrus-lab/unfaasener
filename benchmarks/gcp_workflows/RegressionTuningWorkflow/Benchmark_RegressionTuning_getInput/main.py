from sklearn import datasets
import base64
import json
import datetime
import logging
import uuid
from random import randint
from sys import getsizeof
from google.cloud import datastore
from google.cloud import pubsub_v1
import numpy as np
import random


def getInput(request):
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        samplesNum =  request.args.get('message')
    elif request_json and 'message' in request_json:
        samplesNum =  request_json['message']
    reqID = uuid.uuid4().hex
    message_json = json.dumps({
      'data': {'samplesNum': samplesNum, 'reqID' : reqID},
    })

    logging.info(message_json)

    return message_json
