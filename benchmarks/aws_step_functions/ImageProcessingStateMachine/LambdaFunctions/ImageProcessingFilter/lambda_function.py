import json
import boto3
import uuid
from datetime import datetime
import os
import base64
import logging
from PIL import Image, ImageFilter

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    
    # Get input
    print("Filter function")
    print(event)
    fileName = json.loads(event['body'])['data']['imageName']
    print(fileName)
    bucket = s3.Bucket('imageprocessingbenchmark')
    path_list = json.loads(event['body'])['data']['path_list']
    
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform filter
    img = image.filter(ImageFilter.BLUR)
    path = "/tmp/" + "blur-" + fileName
    img.save(path)
    path_list.append(path)

    img = image.filter(ImageFilter.CONTOUR)
    path = "/tmp/" + "contour-" + fileName
    img.save(path)
    path_list.append(path)

    img = image.filter(ImageFilter.SHARPEN)
    path = "/tmp/" + "sharpen-" + fileName
    img.save(path)
    path_list.append(path)

    # Upload results
    bucket.upload_file("/tmp/blur-" + fileName, "blur-" + fileName)
    bucket.upload_file("/tmp/contour-" + fileName, "contour-" + fileName)
    bucket.upload_file("/tmp/sharpen-" + fileName, "sharpen-" + fileName)
    
    # Clean up
    os.remove("/tmp/blur-" + fileName)
    os.remove("/tmp/contour-" + fileName)
    os.remove("/tmp/sharpen-" + fileName)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': fileName, 'path_list': path_list},
        })
    }
