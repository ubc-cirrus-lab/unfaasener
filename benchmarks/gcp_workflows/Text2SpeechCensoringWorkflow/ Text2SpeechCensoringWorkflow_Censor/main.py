import base64
from datetime import datetime
import requests 
import logging
import uuid
import numpy as np
from sys import getsizeof
from pydub import AudioSegment
from io import BytesIO
import os
import json
from google.cloud import storage
from ast import literal_eval

def censor(request):
    request_json = request.get_json()
    reqID = request_json['reqID']
    fileName = request_json['convertedFileName']
    indexes = request_json['indexes']
    Text2SpeechCensoringWorkflow_Censor(fileName, indexes, reqID)

    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'reqID': reqID},
          }
      } 


def Text2SpeechCensoringWorkflow_Censor(fileName, indexes, reqID):
    indexes = literal_eval(indexes)
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    file = open("/tmp/"+fileName, 'rb').read()
    file = BytesIO(file)
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    #reset file
    file.seek(0)
    outputfile=BytesIO()
    speech = AudioSegment.from_wav(file)
    
    samples = np.array(speech.get_array_of_samples())
    # efficient implementation
    #for start, end in indexes:
    #    start_sample = int(start*len(samples))
    #    end_sample = int(end*len(samples))
    #    samples[start_sample:end_sample] = [0]
    
    # we use the inefficient implementation here
    for index, s in enumerate(samples):
        for start, end in indexes:
            start_sample = int(start*len(samples))
            end_sample = int(end*len(samples))
            if index > start_sample and index < end_sample:
                samples[index] = 0
    
    new_sound = speech._spawn(samples)
    new_sound.export(outputfile, format="wav")      
    result =  outputfile.getvalue()
    newFileName = str(uuid.uuid4())
    newFileName = "Final, "+newFileName+".wav"
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    os.remove("/tmp/"+newFileName)
    logging.warning(reqID)
    blobs = storage_client.list_blobs("text2speecstorage")

    for blob in blobs:
        if (reqID) in (blob.name):
            blob = bucket.blob(blob.name)
            blob.delete()