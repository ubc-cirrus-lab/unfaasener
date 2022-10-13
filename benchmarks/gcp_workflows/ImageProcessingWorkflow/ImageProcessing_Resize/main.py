import base64
import datetime
import requests 
import logging
import uuid
import os
import json
from google.cloud import storage
from PIL import Image, ImageFilter
from time import time

def ImageProcessing_Resize(request):
    request_json = request.get_json()
    fileName = json.loads(request_json['message'])['body']['data']['imageName']
    reqID = json.loads(request_json['message'])['body']['data']['reqID']

    if not fileName or not reqID: 
        print("An error happened while extracting the inputs")
        return json.dumps([])
        
    storage_client = storage.Client()
    bucket = storage_client.bucket("imageprocessingworkflowstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+ fileName)
    
    image = Image.open("/tmp/"+fileName)
    image.thumbnail((128, 128))
    path = "/tmp/" + "resized-" + fileName
    image.save(path)
    upPath = "resize-" + fileName
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(path)
    os.remove(path)
    os.remove("/tmp/"+fileName)
    garbage(reqID)

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'imageName': upPath, 'reqID': reqID},
        }
    })

def garbage(reqID):
    storage_client = storage.Client()
    blobs = storage_client.list_blobs("imageprocessingworkflowstorage")
    blobsNames = [blob.name for blob in blobs if reqID in blob.name ]
    bucket = storage_client.bucket("imageprocessingworkflowstorage")

    for blob in blobsNames:
        if not ((blob).startswith("resize-")):
            deletedBlob = bucket.blob(blob)
            deletedBlob.delete()
