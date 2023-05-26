import base64
import datetime
import requests 
import logging
import uuid
from sys import getsizeof
from google.cloud import pubsub_v1
from google.cloud import datastore
from pydub import AudioSegment
from io import BytesIO
import os
import json
from google.cloud import storage


publisher = pubsub_v1.PublisherClient()
# Replace *** with your Google Cloud Project ID
PROJECT_ID = '***'
DSclient = datastore.Client()

def compress(event, context):
    routingData = (event['attributes'])['routing']
    reqID = (event['attributes'])['reqID']
    routing = routingData[5]
    fileName = (json.loads(base64.b64decode(event['data']).decode('utf-8')))['data']['message']

    message2send = Text2SpeechCensoringWorkflow_Compression(fileName,reqID)
    # 0 for serverless, 1 for VM
    message_json = json.dumps({
      'data': {'message': message2send},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-MergingPoint')
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'], routing = routingData.encode("utf-8"), messageContent = "convertedFileName", branchName = "Text2SpeechCensoringWorkflow_Censor", branch = "Text2SpeechCensoringWorkflow_Compression")
      publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber) 
      invokedFunction = "Text2SpeechCensoringWorkflow_MergedFunction"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = (event['attributes'])['reqID'],invokedFunction = invokedFunction, routing = routingData.encode("utf-8"), messageContent = "convertedFileName", branchName = "Text2SpeechCensoringWorkflow_Censor", branch = "Text2SpeechCensoringWorkflow_Compression")
      publish_future.result()

    logging.warning(str(reqID))


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
    


