import json
import boto3
import uuid
from datetime import datetime
import os
import base64
import logging
from PIL import Image, ImageFilter

def lambda_handler(event, context):
    
    # Get input
    msg = event['Records'][0]['Sns']['Message']
    body = (json.loads(msg))['body']
    data = (json.loads(body))['data']
    
    fileName = data['imageName']
    reqID = data['reqID']
    
    s3 = boto3.resource('s3')
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
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'imageName': upPath, 'reqID': reqID},
        })
    })
    
    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:ImageProcessingGrayscale",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }