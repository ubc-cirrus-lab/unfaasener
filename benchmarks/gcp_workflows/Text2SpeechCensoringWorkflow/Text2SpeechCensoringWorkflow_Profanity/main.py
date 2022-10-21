import base64
from io import BytesIO
from datetime import datetime
import requests 
import logging
import uuid
from sys import getsizeof
import os
import json
from google.cloud import storage
from profanity import profanity
from flask import jsonify

def detect(request):
    request_json = request.get_json()
    reqID = request_json['reqID']
    message = request_json['message']
    result = Text2SpeechCensoringWorkflow_Profanity(message)

    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message': str(result), 'reqID': reqID},
          }
      }

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