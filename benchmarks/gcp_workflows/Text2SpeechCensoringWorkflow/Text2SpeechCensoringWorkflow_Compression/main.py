import base64
from datetime import datetime
import requests 
import logging
import uuid
from sys import getsizeof
from pydub import AudioSegment
from io import BytesIO
import os
import json
from google.cloud import storage

def compress(request):
    request_json = request.get_json()
    reqID = request_json['reqID']
    fileName = request_json['message']

    message2send = Text2SpeechCensoringWorkflow_Compression(fileName,reqID)
    
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message': message2send, 'reqID': reqID},
          }
      }


def Text2SpeechCensoringWorkflow_Compression(fileName,reqID):
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    dlFile = open("/tmp/"+fileName, 'rb').read()
    dlFile = BytesIO(dlFile)
        # find out length of file
    dlFile.seek(0, os.SEEK_END)
    file_length = dlFile.tell()
    #reset file
    dlFile.seek(0)
    outputfile=BytesIO()
    speech = AudioSegment.from_wav(dlFile)
    speech = speech.set_frame_rate(5000)
    speech = speech.set_sample_width(1)
    speech.export(outputfile, format="wav")
    
    result =  outputfile.getvalue()
    newFileName = str(uuid.uuid4())+"-"+reqID
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    os.remove("/tmp/"+newFileName)

    message2send = newFileName
    return message2send