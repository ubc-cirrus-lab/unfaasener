import json
from datetime import datetime
import boto3
from sklearn import datasets
import os

s3 = boto3.resource('s3')

def lambda_handler(event, context):
    
    # Get input
    if event == {}:
        print("Error: Event is not provided")
        return
    else :
        msg = event['Records'][0]['Sns']['Message']
        body = (json.loads(msg))['body']
        data = (json.loads(body))['data']
    
        n_samples = data['n_samples']
        reqID = data['reqID']
    
    bucket = s3.Bucket("regression-tuning-storage")
    x, y = datasets.make_regression(n_samples=n_samples,
                                    n_features=1,
                                    n_informative=1,
                                    n_targets=1,
                                    bias=3.0,
                                    noise=1.0)
    # just make sure data is in the right format, i.e. one feature
    assert x.shape[1] == 1
    # write to file, tab separated
    path = "/tmp/" + "dataset.txt"
    with open(path, "w") as _file:
        for _ in range(len(x)):
            _file.write("{}\t{}\n".format(x[_][0], y[_]))
    upPath = str(reqID)+"-dataset.txt"
    bucket.upload_file("/tmp/dataset.txt", upPath)
    os.remove(path)

   # Return
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'n_samples': n_samples, 'upPath': upPath, 'reqID': reqID},
        })
    })
    
    client = boto3.client('sns')
    
    response1 = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:RegressionTuningFirstModel",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
   
    response2 = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:RegressionTuningSecondModel",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
        'statusCode': 200,
        'body': json.dumps({"FirstModelResponse": response1, "SecondModelResponse": response2})
   }