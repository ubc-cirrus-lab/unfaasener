This directory containts the implementation of the RegressionTuning benchmark for AWS Lambda and SNS (Simple Notification Service). 

The subdirectories provide the lambda code for each function of this benchmark, assuming that the user has created the following SNS topics in their AWS account.

| SNS Topic Name  | SNS Topic Type  |
| ------------- | ----- |
| RegressionTuningCreateDataset  | Standard |
| RegressionTuningFirstModel  | Standard |
| RegressionTuningSecondModel  | Standard |
| RegressionTuningMerge  | Standard |
| RegressionTuningJoinRuns  | Standard |