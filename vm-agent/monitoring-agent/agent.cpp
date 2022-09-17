#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>
#include <ring.h>
#include <predictor.h>
#include <procstatparser.h>
#include <dockerprocstatparser.h>
#include <meminfoparser.h>
#include <chrono>
#define _GNU_SOURCE
#include <sched.h>

using namespace std;

void writePrediction(double cpu_pred, double mem_pred)
{
  std::ofstream myfile;
  myfile.open("../../scheduler/resources.txt");
  myfile << cpu_pred;
  myfile << "\n";
  myfile << mem_pred ;
  myfile.close();
}

unsigned int getTotalSystemCores()
{
	return  sysconf(_SC_NPROCESSORS_ONLN);
}

unsigned long long getTotalSystemMemory()
{
    long pages = sysconf(_SC_PHYS_PAGES);
    long page_size = sysconf(_SC_PAGE_SIZE);
    return (pages * page_size)/1024/1024;
}

int handle_prediction_violation(double cpu_pred, double memory_pred)
    {
	    //execute the local scheduler
	    double mem_pred = (100-memory_pred) * getTotalSystemMemory()/100;
            std::cout << "memory  " << mem_pred << std::endl;
            std::cout << "Total number of cores: " << getTotalSystemCores() << std::endl;
            std::cout << "Predicted value:  " << cpu_pred << std::endl;
		    double cores = getTotalSystemCores() * (100 - cpu_pred)/100;
		    std::cout << "cpu  " << cores << std::endl;
                writePrediction(cores, mem_pred);
	    system("cd ../../scheduler/; python3 rpsCIScheduler.py resolve &");

	    return 1;
    }


int main(int, char *[]) {
    int initialFlag = 1;
    size_t ring_size = 10; // keep last 10 records, i.e. 1 second  
    size_t triggerBufferSize = 4;
    size_t triggerBuffer[triggerBufferSize] = {0};
    size_t triggerBufferIndex = 0;
    size_t current_cpu_readings[2]= { 0 };
    size_t current_mem_readings[2]= { 0 };
    float current_docker_reading =  0 ;
    float previous_docker_reading =  0 ;
    size_t previous_readings[2] = { 0 };
    int monitor_intervals = 100000; // in microseconds
    double cpu_pred_old = 0;
    double mem_pred_old = 0;
    double prediction_buffer   = 6; // extra buffer for CPU prediction
    ring cpu_utilization_buffer(ring_size);
    ring mem_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    predictor mem_predictor(&mem_utilization_buffer);
    dockerprocstatparser dockerprocstat; 
    procstatparser procstat(current_cpu_readings);
    meminfoparser memstat(current_mem_readings);
    cpu_set_t  mask;
CPU_ZERO(&mask);
CPU_SET(0, &mask);
int result = sched_setaffinity(0, sizeof(mask), &mask);
    while (true) 
	{
     //get current CPU readings. CPU readings are incremental , so we need to subtract our last readings to get the absoulte CPU utilization
	 procstat.get_proc_stat_times(current_cpu_readings);
 	 current_docker_reading = dockerprocstat.get_proc_stat_times();
	 float idle_diff = current_cpu_readings[0] - previous_readings[0];
	 float total_diff = current_cpu_readings[1] - previous_readings[1];
	 float docker_utilization  = (current_docker_reading - previous_docker_reading);
	 float docker_mem_utilization = dockerprocstat.get_proc_stat_memory();
	 //std::cout << docker_mem_utilization << std::endl;

	 float cpu_utilization = 100.0 * (1.0 - (idle_diff + docker_utilization)/total_diff);
	 previous_docker_reading = current_docker_reading;
	 previous_readings[0] = current_cpu_readings[0];
	 previous_readings[1] = current_cpu_readings[1];
//get current memory readings and generate free memory utilization as percentage
         memstat.get_meminfo(current_mem_readings);
         //std::cout << current_mem_readings[1] << std::endl;

	 float mem_utilization = 100 * ( (float)(current_mem_readings[0]-current_mem_readings[1] - docker_mem_utilization)/ current_mem_readings[0]);
         //std::cout << cpu_utilization << std::endl;
         //std::cout << mem_utilization << std::endl;
//fill the utilziation buffers for the ring_size (i.e. 10 predictions in 1 second)
         if (cpu_utilization_buffer.size() < ring_size) {
                cpu_utilization_buffer.push(double(cpu_utilization));
                mem_utilization_buffer.push(double(mem_utilization));
         }
//once the buffers are full, engage the prediction cycle
         else
         {
                typedef std::chrono::high_resolution_clock Time;
                typedef std::chrono::microseconds us;
                typedef std::chrono::duration<float> fsec;
                auto t0 = Time::now();
                size_t cpu_violation;
                size_t mem_violation;
                if (initialFlag == 1){
                        auto cpu_result = cpu_predictor.compute_predicton_ExponentialMovingAverage((cpu_pred_old),0, 1);
                        cpu_pred_old = cpu_result.prediction;
                        cpu_violation = cpu_result.violation;
		        auto mem_result = mem_predictor.compute_predicton_ExponentialMovingAverage((mem_pred_old),1, 1);
                        mem_pred_old = mem_result.prediction;
                        mem_violation = mem_result.violation;
                        initialFlag = 0;
                        handle_prediction_violation(cpu_pred_old, mem_pred_old);
                }
                else
                {
                        auto cpu_result = cpu_predictor.compute_predicton_ExponentialMovingAverage((cpu_pred_old),0, 0);
                        cpu_pred_old = cpu_result.prediction;
                        cpu_violation = cpu_result.violation;
                        auto mem_result = mem_predictor.compute_predicton_ExponentialMovingAverage((mem_pred_old),1, 0);
                        mem_pred_old = mem_result.prediction;
                        mem_violation = mem_result.violation;
                }
                std::cout << "Total Prediction "<< cpu_pred_old <<"% of CPU consumption in the next window "<<std::endl;
                std::cout << "Total Prediction "<< mem_pred_old <<"% of Memory consumption in the next window "<<std::endl;
                
                if ((cpu_violation==1) || (mem_violation==1))
                        triggerBuffer[triggerBufferIndex] = 1;
                else
                        triggerBuffer[triggerBufferIndex] = 0;
                triggerBufferIndex = (triggerBufferIndex + 1) % triggerBufferSize;
                
                // Check if the trigger buffer has sufficient violations
                size_t recentViols = 0;
                for (int i=0; i<triggerBufferSize; i++) {
                        if (triggerBuffer[i]!=0)
                                recentViols ++;
                }
                if (recentViols >= int(0.5*triggerBufferSize)) {
                        std::cout << "Violation Has Occured!" << std::endl;
                        handle_prediction_violation(cpu_pred_old, mem_pred_old);
                }
                auto t1 = Time::now();
                fsec fs = t1 - t0;
                us d = std::chrono::duration_cast<us>(fs);
                //std::cout <<"Time taken to generate a prediction "<< d.count() << "us\n";
         }
 
//wait for the next monitor_interval to repreat this cycle
	usleep(monitor_intervals);
//communicate the collected prediciton via http
        typedef std::chrono::high_resolution_clock Time;
        typedef std::chrono::microseconds us;
        typedef std::chrono::duration<float> fsec;
//measure the time taken to communicate that prediction via http
        auto t0 = Time::now();
        auto t1 = Time::now();
        fsec fs = t1 - t0;
        us d = std::chrono::duration_cast<us>(fs);
       // std::cout <<"Time taken to transmit the prediction "<< d.count() << "us\n";
        //std::cout <<"#####################################################\n";
	}

}
