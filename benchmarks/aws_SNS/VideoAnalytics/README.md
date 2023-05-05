This directory containts the implementation of the VideoAnalytics benchmark for AWS Lambda and SNS (Simple Notification Service). 

The subdirectories provide the lambda code for each function of this benchmark, assuming that the user has created the following SNS topics in their AWS account.

| SNS Topic Name  | SNS Topic Type  |
| ------------- | ----- |
| VideoAnalytics_Streaming  | Standard |
| VideoAnalytics_Decoder  | Standard |
| VideoAnalytics_Recognisiton  | Standard |