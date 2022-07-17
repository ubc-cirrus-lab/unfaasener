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

def ImageProcessing_Rotate(request):
    request_json = request.get_json()
    fileName = request_json['message']
    if not fileName: 
        print("An error happened while extracting the file name")
        return json.dumps([])
    
    path_list = []
    storage_client = storage.Client()
    bucket = storage_client.bucket("imageprocessingworkflowstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+ fileName)
    image = Image.open("/tmp/"+fileName)
    img = image.transpose(Image.ROTATE_90)
    path = "/tmp/" + "rotate-90-" + fileName
    img.save(path)
    path_list.append(path)

    img = image.transpose(Image.ROTATE_180)
    path = "/tmp/" + "rotate-180-" + fileName
    img.save(path)
    path_list.append(path)

    img = image.transpose(Image.ROTATE_270)
    path = "/tmp/" + "rotate-270-" + fileName
    img.save(path)
    path_list.append(path)

    return json.dumps(path_list)