import json
from datetime import datetime
import boto3
import os
import sys
import io
from PIL import Image
import torch
from torchvision import transforms
import torchvision.models as models

bucket_name = 'videoanalyticsbenchmark'

def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
    img = transform(img)
    return torch.unsqueeze(img, 0)


class ObjectRecognition:
    def __init__(self):
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket('videoanalyticsbenchmark')
        self.bucket_name = 'videoanalyticsbenchmark'
        with open('imagenet_labels.txt', 'r') as f:
            labels = [i for i in f]
        self.labels = labels

        model = models.squeezenet1_1()
        model_file_path = '/tmp/model.pth'
        self.bucket.download_file('squeezenet1_1-b8a52dc0.pth', model_file_path)
        #blob = self.bucket.blob('squeezenet1_1-b8a52dc0.pth')
        #blob.download_to_filename(model_file_path)
        model.load_state_dict(torch.load(model_file_path))
        self.model = model
        os.remove(model_file_path)

    def infer(self, key):

        obj = self.s3.Object(bucket_name=self.bucket_name, key=key)
        response = obj.get()
        frame = response['Body'].read()
        print(f'frame is {frame}')
        frame = preprocess_image(frame)

        self.model.eval()
        with torch.no_grad():
            out = self.model(frame)
        _, indices = torch.sort(out, descending=True)
        percentages = torch.nn.functional.softmax(out, dim=1)[0] * 100

        return ','.join([f'{self.labels[idx]}: {percentages[idx].item()}%' for idx in indices[0][:5]]).strip()

def lambda_handler(event, context):
    msg = event['Records'][0]['Sns']['Message']
    data = (json.loads(msg))['data']

    image_name = data['imageName']
    req_id = data['reqID']

    VideoAnalytics_Recognition(image_name, req_id)

    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'reqID': req_id},
        })
    }

def VideoAnalytics_Recognition(image_name, req_id):
    m = ObjectRecognition()
    result = m.infer(image_name)
    result_filename = f'{req_id}-{image_name}'
    s3 = boto3.resource('s3')
    s3object = s3.Object(bucket_name=bucket_name, key=result_filename)
    s3object.put(Body=result)