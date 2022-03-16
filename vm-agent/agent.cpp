#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>
#include <ring.h>
#include <predictor.h>
#include <procstatparser.h>
#include <meminfoparser.h>
#include <chrono>

using namespace std;
int main(int, char *[]) {

    size_t ring_size=10; // keep last 10 records, i.e. 1 second  
    size_t current_cpu_readings[2]= { 0 };
    size_t current_mem_readings[2]= { 0 };
    size_t previous_readings[2] = { 0 };
    int monitor_intervals=100000; // 100ms in microseconds
    double prediction_buffer   = 6; //extra buffer for CPU prediction
    ring cpu_utilization_buffer(ring_size);
    ring mem_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    predictor mem_predictor(&mem_utilization_buffer);
    procstatparser procstat(current_cpu_readings);
    meminfoparser memstat(current_mem_readings);
    while (true) 
	{
//get current CPU readings. CPU readings are incremental , so we need to subtract our last readings to get the absoulte CPU utilization
	 procstat.get_proc_stat_times(current_cpu_readings);
	 float idle_diff = current_cpu_readings[0] - previous_readings[0];
	 float total_diff = current_cpu_readings[1] - previous_readings[1];
	 float cpu_utilization = 100.0 * (1.0 - idle_diff/total_diff);
	 previous_readings[0] = current_cpu_readings[0];
	 previous_readings[1] = current_cpu_readings[1];
//get current memory readings and generate free memory utilization as percentage
         memstat.get_meminfo(current_mem_readings);
	 float mem_utilization = 100 * ( (float)current_mem_readings[1] / current_mem_readings[0]);
         std::cout << cpu_utilization << std::endl;
         std::cout << mem_utilization << std::endl;
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
                std::cout << "Total Prediction "<< cpu_predictor.compute_predicton() + prediction_buffer <<"% of CPU consumption in the next window "<<std::endl;
                std::cout << "Total Prediction "<< mem_predictor.compute_predicton() + prediction_buffer <<"% of Memory consumption in the next window "<<std::endl;
                auto t1 = Time::now();
                fsec fs = t1 - t0;
                us d = std::chrono::duration_cast<us>(fs);
                std::cout <<"Time taken to generate a prediction "<< d.count() << "us\n";
                std::cout <<"#####################################################\n";

         }
 
//wait for the next monitor_interval to repreat this cycle
	usleep(monitor_intervals);
	


	}


}

