## First Run 
```
{
    "lambdaARN": "arn:aws:lambda:us-east-2:**********:function:ImageProcessingFlip",
    "powerValues": [128, 256, 512, 1024, 2048, 3008],
    "num": 20,
    "payload": "{}",
    "parallelInvocation": true,
    "strategy": "cost"
}
```
Result of it is as below: 

```
{
  "power": 256,
  "cost": 0.0000040488,
  "duration": 963.3116666666666,
  "stateMachine": {
    "executionCost": 0.0003,
    "lambdaCost": 0.0018475359000000003,
    "visualization": "https://lambda-power-tuning.show/#gAAAAQACAAQACMAL;nUT0RPLTcETyuyFE2vjSQ0sWs0M6lb9D;+sGJNu3ahzaUXLY2M+PtNp1fSjet9543"
  }
}

```

<img src="first_run.png"
     style="float: center;" />

## Second Run 
```
{
    "lambdaARN": "arn:aws:lambda:us-east-2:**********:function:ImageProcessingFlip",
    "powerValues": [128, 152, 176, 200, 224, 248, 272, 296, 320, 344, 368, 392, 416, 440, 464, 488, 512]
    "num": 20,
    "payload": "{}",
    "parallelInvocation": true,
    "strategy": "cost"
}
```
Result of it is as below: 

```
{
  "power": 224,
  "cost": 0.0000042189,
  "duration": 1147.9291666666668,
  "stateMachine": {
    "executionCost": 0.00057,
    "lambdaCost": 0.0026677775249999997,
    "visualization": "https://lambda-power-tuning.show/#gACYALAAyADgAPgAEAEoAUABWAFwAYgBoAG4AdAB6AEAAg==;EZkYRSYV3kRZDs9EGPMLRbx9j0QDKYdEVa+DRII4okSgLYhE77SSROiwekQ61VxEhaudRDPvUkR0+mpEgkpvRKTwRUQ=;5xKsNmKxlDZLi6A2BaD2NhOQjTY4uJM2i9KdNueB0zbnA8A23lLeNlExyza2w742M4EQN0BvzDZtG/A2WK4ANx473zY="
  }
}

```

<img src="second_run.png"
     style="float: center;" />

## Third Run 
```
{
    "lambdaARN": "arn:aws:lambda:us-east-2:**********:function:ImageProcessingFlip",
    "powerValues": [192, 196, 200, 204, 208, 212, 216, 220, 224, 228, 232, 236, 240, 244, 248, 252, 256],
    "num": 20,
    "payload": "{}",
    "parallelInvocation": true,
    "strategy": "cost"
}
```
Result of it is as below: 

```
{
  "power": 244,
  "cost": 0.000001084846875,
  "duration": 270.73083333333335,
  "stateMachine": {
    "executionCost": 0.00057,
    "lambdaCost": 0.002344071975,
    "visualization": "https://lambda-power-tuning.show/#wADEAMgAzADQANQA2ADcAOAA5ADoAOwA8AD0APgA/AAAAQ==;Ji/RRClAv0T5IcVEA3u8RCb1sUTs+7dEUjTiRIyJ30STs5hEUgkFRX7HrUSkSp5E0DGyRIxdh0NI+aVEq+ypRN5rq0Q=;lu+wNksxpTYSva02J1qpNu4Noza/yqs2cznXNq+q2DYcsJY2OJwFN1unsTZZm6Q2aWe8Ng6bkTX+TbU2Dqu8NqRawTY="
  }
}

```

<img src="third_run.png"
     style="float: center;" />

## Fourth Run 
```
{
    "lambdaARN": "arn:aws:lambda:us-east-2:**********:function:ImageProcessingFlip",
    "powerValues": [220, 222, 224, 226, 228, 230, 232, 234, 236, 238, 240, 242, 244, 246, 248, 250, 252, 254, 256, 258],
    "num": 20,
    "payload": "{}",
    "parallelInvocation": true,
    "strategy": "cost"
}
```
Result of it is as below: 

```
{
  "power": 256,
  "cost": 0.0000043302000000000005,
  "duration": 1030.8875,
  "stateMachine": {
    "executionCost": 0.00065,
    "lambdaCost": 0.0030033324562499996,
    "visualization": "https://lambda-power-tuning.show/#3ADeAOAA4gDkAOYA6ADqAOwA7gDwAPIA9AD2APgA+gD8AP4AAAECAQ==;/brdRBE3vkSJILNEcfeiRGCmokTUaLNE78C7RHvEx0S/eKdEpyO2RFwVGUXQw5JEfk3bRLxt8ETaupdEw62RRGqNsUSrrJxEZtyARCYjmEQ=;n9nWNoYBujaH1LA2OjyiNoFrozbn0bU2PvW/NrL6zTZEF642ywa/NgPZITcNiZw2dLzrNgpHAjepvaU2sXigNmkhxTYFWK82I0yRNvn9rDY="
  }
}

```

<img src="fourth_run.png"
     style="float: center;" />

## Fifth Run 
```
{
    "lambdaARN": "arn:aws:lambda:us-east-2:**********:function:ImageProcessingFlip",
    "powerValues": [240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258],
    "num": 20,
    "payload": "{}",
    "parallelInvocation": true,
    "strategy": "cost"
}
```
Result of it is as below: 

```
{
  "power": 256,
  "cost": 0.000004389000000000001,
  "duration": 1044.9225,
  "stateMachine": {
    "executionCost": 0.00063,
    "lambdaCost": 0.0031028519812500007,
    "visualization": "https://lambda-power-tuning.show/#8ADxAPIA8wD0APUA9gD3APgA+QD6APsA/AD9AP4A/wAAAQEBAgE=;FOrwRFkEjUQmw6lEdMbQRNoeskSdCQBFLN/URDOBrURScQBFZhrmRNp+0kSPJLtEN9LxREtUAEW8seREv4SlRIWdgkRtetBEk1vURA==;fbr+NiDJlTZSDLU2fYjfNuFovzZvLQo3WqDmNjbevDboWAw38lr8NvLC5zbh/M42zjcGN58JDzdw4v82QQC6NjlFkza3/Os27k7xNg=="
  }
}

```

<img src="fifth_run.png"
     style="float: center;" />


---
**Result**

The best size taken for this lambda function is 256.

---

