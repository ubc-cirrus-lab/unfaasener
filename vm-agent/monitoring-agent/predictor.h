#include <vector>
#include <stdexcept>
#include <cmath>
class predictor
{

    ring* utilization_records;
    double sum,standardDeviation = 0.0,mean = 0.0;
    int size;
public:
    predictor(ring* buffer)
    {
        utilization_records = buffer;
	sum=0;
    }
    double compute_predicton() 
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

    

};
