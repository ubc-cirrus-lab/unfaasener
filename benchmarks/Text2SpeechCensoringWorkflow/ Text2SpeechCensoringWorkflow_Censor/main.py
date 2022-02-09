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


publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def censor(event, context):
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
    routing = int(routingData[4])
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['newFile']
    indexes = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['indexes']
    # print("filename:{}".format(fileName))
    # print("prev indexes:{}".format((indexes)))
    # indexess = json.dumps(indexesMsg)
    indexes = literal_eval(indexes)
    # print("indexes:{}".format((indexes)))
    # print("type:{}".format(type(indexes)))
    
    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+fileName)
    file = open("/tmp/"+fileName, 'rb').read()
        # find out length of file
    file = BytesIO(file)
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    #reset file
    file.seek(0)
    # print("Inputfilesize: "+str(file_length))
    # print("Length of Input-Indexes: "+str(len(indexes)))
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
          
    # print file lengths
    # print("Outputfilesize: "+str(len(outputfile.getvalue())))
    
    result =  outputfile.getvalue()
    newFileName = str(uuid.uuid4())
    newFileName = "Final, "+newFileName+".wav"
    with open("/tmp/"+newFileName, "wb") as outfile:
        outfile.write(result)

    storage_client = storage.Client()
    bucket = storage_client.bucket("text2speecstorage")
    blob = bucket.blob(newFileName)
    blob.upload_from_filename("/tmp/"+newFileName)
    # print(
    #     "File {} uploaded to {}.".format(
    #         "/tmp/"+newFileName, newFileName
    #     ))
    os.remove("/tmp/"+newFileName)
    logging.warning((event['attributes'])['reqID'])
    blobs = storage_client.list_blobs("text2speecstorage")

    for blob in blobs:
        if ((event['attributes'])['reqID']) in (blob.name):
            blob = bucket.blob(blob.name)
            blob.delete()
            


