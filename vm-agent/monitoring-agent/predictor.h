#include <vector>
#include <stdexcept>
#include <cmath>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <iostream>
#include <fstream>

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
    double compute_predicton_ExponentialMovingAverage(double x,int type)
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
            handle_prediction_violation(prediction,type);
    }

    return  prediction;
    }

    int handle_prediction_violation(double pred, int type)
    {
	    //execute the local scheduler
	    if ( type == 1) //memory 
	    {
	    double memory_pred = (100-pred) * getTotalSystemMemory()/100;
            std::cout<<"memory  "<<memory_pred<<std::endl;
            writePrediction(memory_pred,type);
	    }

	    if (type == 0)//cpu
	    {
		    int cores=getTotalSystemCores() * (100 - pred)/100;
		    std::cout<<"cpu  "<<cores<<std::endl;
                    writePrediction(cores,type);

	    }
	    // std::ifstream lockopen("/tmp/lock");
        // if (lockopen.fail()) {
	    system("cd ../../scheduler/; python3 rpsCIScheduler.py resolve &");
	    // }
	    return 1;
    }

unsigned long long getTotalSystemMemory()
{
    long pages = sysconf(_SC_PHYS_PAGES);
    long page_size = sysconf(_SC_PAGE_SIZE);
    return (pages * page_size)/1024/1024;
}
    
unsigned int getTotalSystemCores()
{
	return  sysconf(_SC_NPROCESSORS_ONLN);
}
 void writePrediction(double pred,int type)
{
  std::fstream file;
  std::ofstream myfile;
  std::string line;
  std::string line2;
  file.open ("../../scheduler/resources.txt");
  getline(file,line);
  getline(file,line2);
  file.close();
  myfile.open ("../../scheduler/resources.txt");
  if (type == 1 )
  {
  myfile << line;
  myfile << "\n";
  myfile << pred ;
  myfile.close();
  }
  if (type == 0)
  {
  myfile << pred ;
  myfile << "\n";
  myfile << line2;
  myfile.close();

  }

}

};
