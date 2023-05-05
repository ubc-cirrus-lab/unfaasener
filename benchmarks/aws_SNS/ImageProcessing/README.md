This directory containts the implementation of the ImageProcessing benchmark for AWS Lambda and SNS (Simple Notification Service). 

The subdirectories provide the lambda code for each function of this benchmark, assuming that the user has created the following SNS topics in their AWS account.

| SNS Topic Name  | SNS Topic Type  |
| ------------- | ----- |
| ImageProcessingFilter  | Standard |
| ImageProcessingFlip  | Standard |
| ImageProcessingGrayscale  | Standard |
| ImageProcessingResize  | Standard |
| ImageProcessingRotate  | Standard |