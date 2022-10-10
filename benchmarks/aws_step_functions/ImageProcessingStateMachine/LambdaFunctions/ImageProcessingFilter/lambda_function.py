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
    if event == {}:
        fileName = 'sample_2.png'
        reqID = '111'
    else:
        fileName = json.loads(event['body'])['data']['imageName']
        reqID = json.loads(event['body'])['data']['reqID']
    
    bucket = s3.Bucket('imageprocessingbenchmark')
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform filter
    img = image.filter(ImageFilter.BLUR)
    path = "/tmp/" + "blur-" + fileName
    upPath = reqID + "blur-" + fileName
    img.save(path)

    # Upload results
    bucket.upload_file(path, upPath)
    
    # Clean up
    os.remove("/tmp/blur-" + fileName)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': upPath, 'reqID': reqID},
        })
    }