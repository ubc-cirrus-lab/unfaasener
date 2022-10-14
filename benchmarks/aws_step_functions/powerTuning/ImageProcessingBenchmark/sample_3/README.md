### This benchmark was originally taken from the following github repository: https://github.com/kmu-bigdata/serverless-faas-workbench

#### We modified the code for our own purposes.

## Power Tuning Results 

The sample image used for this expriemnt had the following properties:
- Type: jpg
- Size: 14 KB
- Grayscale

This is the summary of the lambda memory size values after power tuning. 

| Function Name            | Memory Size (MB) |
|--------------------------|------------------|
| ImageProcessingGetInput  | 128              |
| ImageProcessingFlip      | 216              |
| ImageProcessingRotate    | 148              |
| ImageProcessingFilter    | 232              |
| ImageProcessingGrayscale | 144              |
| ImageProcessingResize    | 206              |


