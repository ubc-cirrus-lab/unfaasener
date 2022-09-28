import json
import boto3
import uuid
from datetime import datetime
from PIL import Image
import os

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    
    # Get input
    print("Flip function")
    
    if event == {}:
        fileName = 'test.png'
    else: 
        fileName = json.loads(event['body'])['data']['imageName']
    
    
    bucket = s3.Bucket('imageprocessingbenchmark')
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform flip
    path = "/tmp/flip-left-right-" + fileName
    upPath = "flip-left-right-" + fileName
    img = image.transpose(Image.FLIP_LEFT_RIGHT)
    img = image.transpose(Image.FLIP_LEFT_RIGHT)
    img.save(path)

    # Upload results
    bucket.upload_file(path, upPath)
    
    # Clean up
    os.remove(path)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': upPath},
        })
    }