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
    print("Roatate function")
    print(event)
    fileName = json.loads(event['body'])['data']['imageName']
    print(fileName)
    bucket = s3.Bucket('imageprocessingbenchmark')
    path_list = json.loads(event['body'])['data']['path_list']
    
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform rotate
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

    # Upload results
    bucket.upload_file("/tmp/rotate-90-" + fileName, "rotate-90-" + fileName)
    bucket.upload_file("/tmp/rotate-180-" + fileName, "rotate-180-" + fileName)
    bucket.upload_file("/tmp/rotate-270-" + fileName, "rotate-270-" + fileName)
    
    # Clean up
    os.remove("/tmp/rotate-90-" + fileName)
    os.remove("/tmp/rotate-180-" + fileName)
    os.remove("/tmp/rotate-270-" + fileName)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': fileName, 'path_list': path_list},
        })
    }
