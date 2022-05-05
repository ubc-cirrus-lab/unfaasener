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

def ImageProcessing_Flip(request):
    request_json = request.get_json()
    print(request_json['message'])
    fileName = request_json['message']
    if not fileName: 
        print("An error happened while extracting the file name")
        return json.dumps([])
    print(fileName)
    path_list = []
    storage_client = storage.Client()
    bucket = storage_client.bucket("imageprocessingworkflowstorage")
    blob = bucket.blob(fileName)
    blob.download_to_filename("/tmp/"+ fileName)
    image = Image.open("/tmp/"+fileName)
    img = image.transpose(Image.FLIP_LEFT_RIGHT)
    path = "/tmp/" + "flip-left-right-" + fileName
    img.save(path)
    path_list.append(path)

    img = image.transpose(Image.FLIP_TOP_BOTTOM)
    path = "/tmp/" + "flip-top-bottom-" + fileName
    img.save(path)
    path_list.append(path)

    return json.dumps(path_list)