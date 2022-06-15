#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>

class meminfoparser
{
//    size_t results[2];
public:
    meminfoparser(size_t* results)
    {
	results[0] = 0; //total memory
	results[1] = 0; // free memory
    }
    bool get_meminfo(size_t* results) 
    {
     std::string token;
     std::ifstream meminfo("/proc/meminfo");
     std::string memtotal;
     std::string memfree;
     while(meminfo >> token)
     {
	if ( token == "MemTotal:")
	{	
		meminfo >> results[0];
//		std::cout << "MemFotal: " << results[0] << ")\n";	
	}
	if ( token == "MemAvailable:" )
	{
		meminfo >> results[1];
//               std::cout << "MemFree: " << results[1] << ")\n";

	}

     }
     return true;
    }
    

};
