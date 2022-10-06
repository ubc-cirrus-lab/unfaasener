#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>
#include <sstream>


class dockerprocstatparser
{
//    size_t results[2];
public:
    dockerprocstatparser()
    {
     size_t a;
    }
    float get_proc_stat_times(int pid) 
    {
     std::ifstream in;
     std::string line;
     std::string utime= "0";
     std::string ktime="0";
     in.open("/proc/"+std::to_string(pid)+"/stat");
    if(in.is_open())
    {
        while(std::getline(in, line))
        {
            std::istringstream iss(line); 
	    std::string tokens;
	    std::string parsed;

for (int i = 0; i < 15; ++i)
{
	iss>>parsed;
  if (i==12)
  {
	iss >> utime;
	iss>>ktime;
  }
}
//  std::cout << utime << std::endl;
///    std::cout << ktime << std::endl;
	}
    }
     return std::stof(utime) + std::stof(ktime);
    }
    
    float get_proc_stat_memory(int pid)
{

     std::ifstream in;
     std::string line;
     std::string allocatedmem="0" ;
     std::string ktime="0";
     in.open("/proc/"+std::to_string(pid)+"/statm");
    if(in.is_open())
    {
        while(std::getline(in, line))
        {
            std::istringstream iss(line);
            std::string tokens;
            std::string parsed;

        iss>>allocatedmem;
  }
}
float memkb=stof(allocatedmem);
memkb = (memkb)*4;
return memkb  ;
}


};
