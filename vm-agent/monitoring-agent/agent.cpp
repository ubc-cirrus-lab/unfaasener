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
#include <communicator.h>
#include <chrono>

using namespace std;
int main(int, char *[]) {

    size_t ring_size=10; // keep last 10 records, i.e. 1 second  
    size_t current_cpu_readings[2]= { 0 };
    size_t current_mem_readings[2]= { 0 };
    float current_docker_reading =  0 ;
    float previous_docker_reading =  0 ;
    size_t previous_readings[2] = { 0 };
    int monitor_intervals=100000; // 100ms in microseconds
    double cpu_pred_old =0;
    double mem_pred_old =0;
    double prediction_buffer   = 6; //extra buffer for CPU prediction
    communicator com;
    ring cpu_utilization_buffer(ring_size);
    ring mem_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    predictor mem_predictor(&mem_utilization_buffer);
    dockerprocstatparser dockerprocstat; 
    procstatparser procstat(current_cpu_readings);
    meminfoparser memstat(current_mem_readings);
    while (true) 
	{
//get current CPU readings. CPU readings are incremental , so we need to subtract our last readings to get the absoulte CPU utilization
	 procstat.get_proc_stat_times(current_cpu_readings);
 	 current_docker_reading = dockerprocstat.get_proc_stat_times();
	 float idle_diff = current_cpu_readings[0] - previous_readings[0];
	 float total_diff = current_cpu_readings[1] - previous_readings[1];
	 float docker_utilization  = (current_docker_reading - previous_docker_reading);
	 float docker_mem_utilization = dockerprocstat.get_proc_stat_memory();
	 std::cout << docker_mem_utilization << std::endl;

	 float cpu_utilization = 100.0 * (1.0 - (idle_diff + docker_utilization)/total_diff);
	 previous_docker_reading = current_docker_reading;
	 previous_readings[0] = current_cpu_readings[0];
	 previous_readings[1] = current_cpu_readings[1];
//get current memory readings and generate free memory utilization as percentage
         memstat.get_meminfo(current_mem_readings);
         std::cout << current_mem_readings[1] << std::endl;

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
		cpu_pred_old = cpu_predictor.compute_predicton_ExponentialMovingAverage((cpu_pred_old));
		mem_pred_old = mem_predictor.compute_predicton_ExponentialMovingAverage((mem_pred_old));
                std::cout << "Total Prediction "<< cpu_pred_old <<"% of CPU consumption in the next window "<<std::endl;
                std::cout << "Total Prediction "<< mem_pred_old <<"% of Memory consumption in the next window "<<std::endl;
                auto t1 = Time::now();
                fsec fs = t1 - t0;
                us d = std::chrono::duration_cast<us>(fs);
                //std::cout <<"Time taken to generate a prediction "<< d.count() << "us\n";
               // std::cout <<"#####################################################\n";

         }
 
//wait for the next monitor_interval to repreat this cycle
	usleep(monitor_intervals);
//communicate the collected prediciton via http
        typedef std::chrono::high_resolution_clock Time;
        typedef std::chrono::microseconds us;
        typedef std::chrono::duration<float> fsec;
//measure the time taken to communicate that prediction via http
        auto t0 = Time::now();
	com.sendprediction();
        auto t1 = Time::now();
        fsec fs = t1 - t0;
        us d = std::chrono::duration_cast<us>(fs);
       // std::cout <<"Time taken to transmit the prediction "<< d.count() << "us\n";
        //std::cout <<"#####################################################\n";

	


	}


}

