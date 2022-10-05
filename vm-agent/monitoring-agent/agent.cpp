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
#include <cmath>
#include <pstream.h>
#include <string>
#include <iostream>
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
    size_t hardTriggerBufferSize = 4;
    size_t hardTriggerBuffer[hardTriggerBufferSize] = {0};
    size_t hardTriggerBufferIndex = 0;
    short int softTriggerVote = 0;
    size_t current_cpu_readings[2]= { 0 };
    size_t current_mem_readings[2]= { 0 };
    float current_docker_reading[100] = { 0} ;
    int containerd_pids[100] =  {0 };
    float previous_docker_reading[100] = { 0 };
    float docker_utilization[100] = { 0} ;
    float docker_mem_utilization[100] = { 0} ;
    float prev_docker_utilization = 0 ;
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
	 redi::ipstream proc("ps -u bin -o pid=", redi::pstreams::pstdout | redi::pstreams::pstderr);
	   std::string line;
	   int processcount=0;
	   current_docker_reading[100] = {0};

     while (std::getline(proc.out(), line))
     {

//     std::cout << "stdout: " << line << '\n';
     containerd_pids[processcount] = stoi(line);
     current_docker_reading[processcount] = dockerprocstat.get_proc_stat_times(containerd_pids[processcount]);
  //   std::cout << current_docker_reading[processcount] << std::endl;

     docker_utilization[processcount]  = (current_docker_reading[processcount] - previous_docker_reading[processcount]);
     docker_mem_utilization[processcount] = dockerprocstat.get_proc_stat_memory(containerd_pids[processcount]);
     previous_docker_reading[processcount] = docker_utilization[processcount];
     processcount++;
     }
     if (proc.eof() && proc.fail())
     proc.clear();
     // Sum all docker utilization of the containerd processes 
     float docker_cpusum = 0;
     float docker_memsum = 0;
     docker_cpusum = accumulate(docker_utilization, docker_utilization+100, 0);
     docker_memsum = accumulate(docker_mem_utilization, docker_mem_utilization+100, 0);


	 float idle_diff = current_cpu_readings[0] - previous_readings[0];
	 float total_diff = current_cpu_readings[1] - previous_readings[1];

	 float cpu_utilization = 100.0 * (1.0 - (idle_diff + docker_cpusum/total_diff));
	 previous_docker_reading[0] = current_docker_reading[0];
	 previous_readings[0] = current_cpu_readings[0];
	 previous_readings[1] = current_cpu_readings[1];
//get current memory readings and generate free memory utilization as percentage
         memstat.get_meminfo(current_mem_readings);
         std::cout << docker_cpusum << std::endl;

	 float mem_utilization = 100 * ( (float)(current_mem_readings[0]-current_mem_readings[1] - docker_memsum)/ current_mem_readings[0]);
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
                        hardTriggerBuffer[hardTriggerBufferIndex] = 1;
                else
                        hardTriggerBuffer[hardTriggerBufferIndex] = 0;
                
                // Check if the trigger buffer has sufficient violations
                size_t recentViols = 0;
                for (int i=0; i<hardTriggerBufferSize; i++) {
                        if (hardTriggerBuffer[i]!=0)
                                recentViols ++;
                }
                double lowTriggerThreshold = 0.2;
                double highTriggerThreshold = 0.8;
                double docker_utilization_change_threshold = 1;
                double availableCores = getTotalSystemCores() * (100 - cpu_pred_old)/100;
                // std::cout << "idle_diff:" << idle_diff << std::endl;
                // std::cout << "docker_utilization:" << docker_utilization << std::endl;
                // std::cout << "total_diff:" << total_diff << std::endl;
                // std::cout << "cpu_utilization:" << cpu_utilization << std::endl;
                // std::cout << "cpu_pred_old:" << cpu_pred_old << std::endl;
                // std::cout << "available_num_of_cores:" << availableCores << std::endl;
                if ( ((docker_cpusum/availableCores)  < lowTriggerThreshold) && ( (fabs(docker_cpusum - prev_docker_utilization) )  > docker_utilization_change_threshold) ){
                        std::cout << "Low Load Sensed"<< std::endl;
                        softTriggerVote -= 1;
                }
                else if ( ((docker_cpusum/availableCores) > highTriggerThreshold) && ( (fabs(docker_cpusum - prev_docker_utilization) )  > docker_utilization_change_threshold) ) {
                        std::cout << "High Load Sensed"<< std::endl;
                        softTriggerVote += 1;
                }
                
                if (softTriggerVote > 4) {
                    std::cout << "Triggering scheduler with HIGH LOAD option."<< std::endl;
                    system("cd ../../scheduler/; python3 rpsCIScheduler.py highLoad &");
                    softTriggerVote = 0;
                } else if (softTriggerVote < -4 ) {
                    std::cout << "Triggering scheduler with LOW LOAD option."<< std::endl;
                    system("cd ../../scheduler/; python3 rpsCIScheduler.py lowLoad &");
                    softTriggerVote = 0;
                } else if (recentViols >= int(0.5*hardTriggerBufferSize)) {
                        std::cout << "Triggering scheduler with RESOLVE option."<< std::endl;
                        handle_prediction_violation(cpu_pred_old, mem_pred_old);
                        // reset the buffer
                        for (int i=0; i<hardTriggerBufferSize; i++) {
                            if (hardTriggerBuffer[i]!=0) {
                                hardTriggerBuffer[i] = 0;
                            }
                        }
                }

                // update docker utilixation
                prev_docker_utilization = docker_cpusum;

                hardTriggerBufferIndex = (hardTriggerBufferIndex + 1) % hardTriggerBufferSize;

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
