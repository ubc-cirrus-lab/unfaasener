#include <vector>
#include <stdexcept>
#include <cmath>
#include <stdio.h>
#include <stdlib.h>
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
	sum=0;
    }
    double compute_predicton_ServerMore() 
    {
     mean = 0;
     sum = 0;
     standardDeviation = 0;
     size=utilization_records->size();
     int i = 0;
     double records[size];
     while (utilization_records->size() > 0)
	{
	records[i] = utilization_records->pop();	
	i++;
	}
    //Compute Mean for the records array
    for(i = 0; i < size; ++i) {
	sum += records[i];
    }
    mean = sum/size;
    // Compute Std Dev.
    for(i = 0; i < size; ++i) {
    standardDeviation += pow(records[i] - mean, 2);
    standardDeviation = standardDeviation/size;
    standardDeviation = sqrt(standardDeviation);
    }
    std::cout << "Time window's Mean is  "<< mean <<" and StdDev is "<< standardDeviation << std::endl;
    return  standardDeviation + mean;
    }
    double compute_predicton_ExponentialMovingAverage(double x)
    {
     alpha = 0.8;
     margin = 0.4;
     max = 0;
     size=utilization_records->size();
     int i = 0;
     double records[size];
     while (utilization_records->size() > 0)
        {
        records[i] = utilization_records->pop();
        i++;
        }
    //Compute Max for the records array
    for(i = 0; i < size; ++i) {
        if (records[i] > max)
	{
		max = records[i];
	}

    }

    prediction = (alpha *  max  + (1-alpha)*x );
    if ( prediction * (1+margin) > 100)
    {
	   prediction = 100 ;
    }
    if ( (int(max) > int(x) ) || (prediction > x + 100*margin))
    {
            std::cout<<"Violation Has Occured x = " << x << "and Max is "<< max <<std::endl;
            handle_prediction_violation();
    }

    return  prediction;
    }

    int handle_prediction_violation()
    {
	    //execute the local scheduler
	    system("python3 /home/centos/newrepo/newrepo2/de-serverlessization/scheduler/rpsCIScheduler.py resolve");
	    return 1;
    }


    

};
