#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>
#include <ring.h>
#include <predictor.h>
#include <parser.h>
#include <meminfoparser.h>
#include <chrono>

using namespace std;
int main(int, char *[]) {

    size_t ring_size=10; // keep last 10 records, i.e. 1 second  
    size_t current_readings[2]= { 0 };
    size_t current_mem_readings[2]= { 0 };
    size_t previous_readings[2] = { 0 };
    int monitor_intervals=100000; // 100ms in microseconds
    double prediction_buffer   = 6; //extra buffer for CPU prediction
    ring buffer(ring_size);
    predictor simple(&buffer);
    parser procstat(current_readings);
    meminfoparser memstat(current_mem_readings);
    while (true) 
	{
	 procstat.get_proc_stat_times(current_readings);
         memstat.get_meminfo(current_mem_readings);
	 float idle_diff = current_readings[0] - previous_readings[0];
	 float total_diff = current_readings[1] - previous_readings[1];
	 float utilization = 100.0 * (1.0 - idle_diff/total_diff);
	 previous_readings[0] = current_readings[0];
	 previous_readings[1] = current_readings[1];
	 usleep(monitor_intervals);
         std::cout << utilization << std::endl;
        if (buffer.size() < ring_size) {
                buffer.push(double(utilization));
        }
        else
        {
                typedef std::chrono::high_resolution_clock Time;
                typedef std::chrono::microseconds us;
                typedef std::chrono::duration<float> fsec;
                auto t0 = Time::now();
                std::cout << "Total Prediction "<< simple.compute_predicton() + prediction_buffer <<"% of CPU consumption in the next window "<<std::endl;
                auto t1 = Time::now();
                fsec fs = t1 - t0;
                us d = std::chrono::duration_cast<us>(fs);
                std::cout <<"Time taken to generate a prediction "<< d.count() << "us\n";
                std::cout <<"#####################################################\n";

        }
 
	


	}



}

