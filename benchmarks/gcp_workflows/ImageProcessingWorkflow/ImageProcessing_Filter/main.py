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

def ImageProcessing_Filter(request):
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
    img = image.filter(ImageFilter.BLUR)
    path = "/tmp/" + "blur-" + fileName
    img.save(path)
    upPath = "-blur-" + fileName
    resblob = bucket.blob(upPath)
    resblob.upload_from_filename(path)
    os.remove(path)
    os.remove("/tmp/"+fileName)

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'imageName': upPath, 'reqID': reqID},
        }
    })