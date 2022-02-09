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
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    # print("messageSize:{}".format((event['attributes'])['msgSize']))
    # print("publishedTime:{},identifier:{},messageSize:{}".format((event['attributes'])['publishTime'], (event['attributes'])['identifier'], (event['attributes'])['msgSize']))
    # print(base64.b64decode(event['data']).decode('utf-8'))
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = int(routingData[2])
    message = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']
    result = extract_indexes(filter(message))
    
    # print("MessageSize:" + str(len(message)))
    # print("Number of Profanities:" + str(len(result)))
    # print("Result:" + str(result))
    topic_path = publisher.topic_path(PROJECT_ID, 'Merging')
    message_json = json.dumps({
      'data': {'message': str(result)},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"), messageContent = "indexes",  branchName = "Text2SpeechCensoringWorkflow_Compression", routingIndex = str(3))
    publish_future.result()
    logging.warning((event['attributes'])['reqID'])

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

