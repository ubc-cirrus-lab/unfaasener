#include <vector>
#include <stdexcept>
#include <cmath>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <iostream>
#include <fstream>

using namespace std;

class predictor
{
    ring* utilization_records;
    double sum,standardDeviation = 0.0,mean = 0.0;
    double max,alpha,margin,prediction = 0.0;
    int size;
    
public:
    predictor(ring* buffer)
    {
        utilization_records = buffer;
	    sum = 0;
    }
    
    auto compute_predicton_ExponentialMovingAverage(double x, int type, int initialFlag)
    {
        size_t violation = 0;
        alpha = 0.85;
        margin = 0.2;
        max = 0;
        size = utilization_records->size();
        if (size == 0)
            throw std::logic_error( "Exception: record buffer has size 0!" );
        int i = 0;
        double records[size];
        while (i < size)
        {
            records[i] = utilization_records->pop();
            i++;
        }
        // calculate the max for the records array
        for(i = 0; i < size; ++i) {
            if (records[i] > max)
            {
                max = records[i];
            }
        }
        prediction = (alpha *  max  + (1-alpha)*x );
        if ( prediction * (1+margin) > 100)
        prediction = 100 ;
        if ( (int(max) - int(x) > 100*margin ) || (int(x) - int(max) > 100*margin ) || (prediction > x + 100*margin)|| (prediction + 100 *margin < x ) || (initialFlag == 1))
            violation = 1;
        struct result {double prediction; size_t violation;};
        return result {prediction, violation};
    }
};
