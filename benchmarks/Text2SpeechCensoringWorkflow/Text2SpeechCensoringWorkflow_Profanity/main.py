import base64
from io import BytesIO
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
import os
import json
from google.cloud import storage
from profanity import profanity
from flask import jsonify


publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()
def detect(event, context):
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = routingData[5]
    message = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    result = Text2SpeechCensoringWorkflow_Profanity(message)

    message_json = json.dumps({
      'data': {'message': str(result)},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex


    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-MergingPoint')
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"), messageContent = "indexes", branchName = "Text2SpeechCensoringWorkflow_Censor", branch = "Text2SpeechCensoringWorkflow_Profanity")
      publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber) 
      invokedFunction = "Text2SpeechCensoringWorkflow_MergedFunction"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], msgSize = str(getsizeof(message)),invokedFunction = invokedFunction, routing = routingData.encode("utf-8"), messageContent = "indexes", branchName = "Text2SpeechCensoringWorkflow_Censor", branch = "Text2SpeechCensoringWorkflow_Profanity")
      publish_future.result()

    logging.warning((event['attributes'])['reqID'])

def Text2SpeechCensoringWorkflow_Profanity(message):
    result = extract_indexes(filter(message))
    return result

def filter(text, char="*"):
    profanity.set_censor_characters("*")
    return profanity.censor(text)


def extract_indexes(text, char="*"):
    indexes = []
    in_word = False
    start = 0
    for index, value in enumerate(text):
        if value == char:
            if not in_word:
                # This is the first character, else this is one of many
                in_word = True
                start = index
        else:
            if in_word:
                # This is the first non-character
                in_word = False
                indexes.append(((start-1)/len(text),(index)/len(text)))
    return indexes  





