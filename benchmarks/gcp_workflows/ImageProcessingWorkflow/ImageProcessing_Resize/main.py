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
    path = "/tmp/" + "resized-" + fileName
    image.thumbnail((128, 128))
    image.save(path)
    return json.dumps([path])