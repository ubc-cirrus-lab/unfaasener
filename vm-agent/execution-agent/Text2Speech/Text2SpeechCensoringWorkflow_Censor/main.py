import base64
import datetime
import requests 
import logging
import uuid
import numpy as np
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
from pydub import AudioSegment
from io import BytesIO
import os
import json
from google.cloud import storage
from ast import literal_eval
import sys

publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def censor(event, context):
    event=json.loads(event)
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    #fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['convertedFileName']
    fileName = (event['data'])['data']['convertedFileName']
    indexes = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['indexes']
    Text2SpeechCensoringWorkflow_Censor(fileName, indexes, reqID)


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
            

def main():
    censor(sys.argv[1],sys.argv[2])
if __name__ == '__main__':
    main()


