### This benchmark was originally taken from the following github repository: https://github.com/kmu-bigdata/serverless-faas-workbench

#### We modified the code for our own purposes.

## Power Tuning Results 

The sample image used for this expriemnt had the following properties:
- Type: png
- Size: 1 MB

This is the summary of the lambda memory size values after power tuning. 

| Function Name            | Memory Size (MB) |
|--------------------------|------------------|
| ImageProcessingGetInput  | 128              |
| ImageProcessingFlip      | 175              |
| ImageProcessingRotate    | 184              |
| ImageProcessingFilter    | 248              |
| ImageProcessingGrayscale | 218              |
| ImageProcessingResize    | 166              |


