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
    print(event)
    print(json.loads(event['body']))
    fileName = json.loads(event['body'])['data']['imageName']
    bucket = s3.Bucket('imageprocessingbenchmark')
    path_list = []
    
    bucket.download_file(fileName, '/tmp/' + fileName)
    image = Image.open("/tmp/"+fileName)
   
    # Perform flip
    path = "/tmp/flip-left-right-" + fileName
    img = image.transpose(Image.FLIP_LEFT_RIGHT)
    img.save(path)
    path_list.append(path)

    path = "/tmp/flip-top-bottom-" + fileName
    img = image.transpose(Image.FLIP_TOP_BOTTOM)
    img.save(path)
    path_list.append(path)

    # Upload results
    bucket.upload_file("/tmp/flip-left-right-" + fileName, "flip-left-right-" + fileName)
    bucket.upload_file("/tmp/flip-top-bottom-" + fileName, "flip-top-bottom-" + fileName)
    
    # Clean up
    os.remove("/tmp/flip-left-right-" + fileName)
    os.remove("/tmp/flip-top-bottom-" + fileName)
    os.remove("/tmp/"+fileName)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': fileName, 'path_list': path_list},
        })
    }

