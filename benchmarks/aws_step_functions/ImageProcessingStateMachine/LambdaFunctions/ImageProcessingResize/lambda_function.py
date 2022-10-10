import json
import boto3
import uuid
from datetime import datetime
import os
import base64
import logging
from PIL import Image, ImageFilter

s3 = boto3.resource('s3')
bucket = s3.Bucket('imageprocessingbenchmark')

def lambda_handler(event, context):
    
    # Get input
    print("Resize function")
    if event == {}:
        fileName = 'sample_2.png'
        reqID = '111'
    else:
        fileName = json.loads(event['body'])['data']['imageName']
        reqID = json.loads(event['body'])['data']['reqID']
    
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform filter
    path = "/tmp/" + "resized-" + fileName
    upPath = "Final-" + fileName
    image.thumbnail((128, 128))
    image.save(path)

    # Upload results
    bucket.upload_file(path, upPath)
    
    # Clean up
    os.remove(path)
    os.remove("/tmp/"+fileName)
    garbage(reqID,'imageprocessingbenchmark')
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': upPath, 'reqID': reqID},
        })
    }
    
def garbage(reqID, bucketName):
    for object_summary in bucket.objects.filter(Prefix=reqID):
        s3.Object(bucketName, object_summary.key).delete()