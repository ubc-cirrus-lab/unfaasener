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
    print("GrayScale function")
    print(event)
    fileName = json.loads(event['body'])['data']['imageName']
    print(fileName)
    bucket = s3.Bucket('imageprocessingbenchmark')
    path_list = json.loads(event['body'])['data']['path_list']
    
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform filter
    img = image.convert('L')
    path = "/tmp/" + "gray-scale-" + fileName
    img.save(path)
    path_list.append(path)

    # Upload results
    bucket.upload_file("/tmp/gray-scale-" + fileName, "gray-scale-" + fileName)
    
    # Clean up
    os.remove("/tmp/gray-scale-" + fileName)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': fileName, 'path_list': path_list},
        })
    }
