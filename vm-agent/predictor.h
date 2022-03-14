#include <vector>
#include <stdexcept>
#include <cmath>
class predictor
{

    ring* cpurecords;
    double sum,standardDeviation = 0.0,mean = 0.0;
    int size;
public:
    predictor(ring* buffer)
    {
        cpurecords = buffer;
	sum=0;
    }
    double compute_predicton() 
    {
     mean = 0;
     sum = 0;
     standardDeviation = 0;
     //std::cout << cpurecords->size() <<std::endl;
     size=cpurecords->size();
     int i = 0;
     double records[size];
     while (cpurecords->size() > 0)
	{
	records[i] = cpurecords->pop();	
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
    }
    std::cout << "Time window's Mean is  "<< mean <<" and StdDev is "<< standardDeviation << std::endl;
    return  standardDeviation + mean;
    }

    

};
