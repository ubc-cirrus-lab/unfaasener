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
from pydub import AudioSegment
import os

def convert(request):
    request_json = request.get_json()
    reqID = request_json['reqID']
    fileName = request_json['message']
   
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    dlFile = open("/tmp/"+fileName, 'rb').read()
    input = BytesIO(dlFile)
    inputSize = len(input.getvalue())
    speech = AudioSegment.from_mp3(input)
    output = BytesIO()
    speech.export(output, format="wav")


    result =  output.getvalue()
    newFileName = str(uuid.uuid4())+"-"+reqID
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    os.remove("/tmp/"+newFileName)

    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message': newFileName, 'reqID': reqID},
          }
      }