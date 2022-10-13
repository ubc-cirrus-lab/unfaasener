import base64
import datetime
import io
import json
import logging
import os
from sys import getsizeof
import uuid

from google.cloud import storage
from torchvision import transforms
from PIL import Image
import torch
import torchvision.models as models


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
        client = storage.Client()
        self.bucket = client.bucket('videoanalyticsworkflow-storage')
        with open('imagenet_labels.txt', 'r') as f:
            labels = [i for i in f]
        self.labels = labels

        model = models.squeezenet1_1()
        model_file_path = '/tmp/model.pth'
        blob = self.bucket.blob('squeezenet1_1-b8a52dc0.pth')
        blob.download_to_filename(model_file_path)
        model.load_state_dict(torch.load(model_file_path))
        self.model = model
        os.remove(model_file_path)

    def infer(self, key):
        blob = self.bucket.blob(key)
        frame = blob.download_as_bytes()
        frame = preprocess_image(frame)

        self.model.eval()
        with torch.no_grad():
            out = self.model(frame)
        _, indices = torch.sort(out, descending=True)
        percentages = torch.nn.functional.softmax(out, dim=1)[0] * 100

        return ','.join([f'{self.labels[idx]}: {percentages[idx].item()}%' for idx in indices[0][:5]]).strip()


def recognition(request):
    
    request_json = request.get_json()
    image_name = request_json['imageName']
    req_id = request_json['reqID']
    VideoAnalytics_Recognition(image_name, req_id)

    return json.dumps({
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    })


def VideoAnalytics_Recognition(image_name, req_id):
    m = ObjectRecognition()
    result = m.infer(image_name)

    cli = storage.Client()
    dst_bucket = cli.bucket('videoanalyticsworkflow-storage-result')
    result_filename = f'{req_id}-{image_name}'
    dst_blob = dst_bucket.blob(result_filename)
    dst_blob.upload_from_string(result)