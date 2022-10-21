import base64
from gtts import gTTS
from io import BytesIO
from datetime import datetime
import logging
import uuid
from sys import getsizeof
import os
import json
from google.cloud import storage

def convert(request):
    request_json = request.get_json()
    reqID = request_json['reqID']
    message = request_json['message']
    message2send = Text2SpeechCensoringWorkflow_Text2Speech(message, reqID)


    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message': message2send, 'reqID': reqID},
          }
      }

   

def Text2SpeechCensoringWorkflow_Text2Speech(message, reqID):
    tts = gTTS(text=message, lang='en')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    result = mp3_fp.getvalue()
    fileName = str(uuid.uuid4())+"-"+reqID
    with open("/tmp/"+fileName, "wb") as outfile:
        outfile.write(result)
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.upload_from_filename("/tmp/"+fileName)
    os.remove("/tmp/"+fileName)
    message2send = fileName
    return message2send