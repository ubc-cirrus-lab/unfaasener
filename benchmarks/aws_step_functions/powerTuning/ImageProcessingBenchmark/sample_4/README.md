### This benchmark was originally taken from the following github repository: https://github.com/kmu-bigdata/serverless-faas-workbench

#### We modified the code for our own purposes.

## Power Tuning Results 

The sample image used for this expriemnt had the following properties:
- Type: bmp
- Size: 120 KB

This is the summary of the lambda memory size values after power tuning. 

| Function Name            | Memory Size (MB) |
|--------------------------|------------------|
| ImageProcessingGetInput  | 128              |
| ImageProcessingFlip      | 288              |
| ImageProcessingRotate    | 320              |
| ImageProcessingFilter    | 240              |
| ImageProcessingGrayscale | 216              |
| ImageProcessingResize    | 184              |


