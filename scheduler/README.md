### Sensitivity of the Solver:

The solutions found by the Gekko solver is sensitive to values of RTOL and OTOL, and they need to be adjusted together. A lower RTOL value leads to more precise solutions, but caution must be taken as reducing it too much may result in incorrect solutions by surpassing the computer precision [1].
In our experiments, we found that a value of 1e-13 works for us. Depending on the intended use, host system running the solver, and other factors, adjustments to these values may help you achieve better results.

You can change RTOL and OTOL by modifying the following code:
```
model.options.OTOL = 1e-13
model.options.RTOL = 1e-13
```

#### References:
[1] https://gekko.readthedocs.io/en/latest/global.html
