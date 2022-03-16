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
		meminfo >> memtotal;
		std::cout << "MemFotal: " << memtotal << ")\n";	
	}
	if ( token == "MemFree:" )
	{
		meminfo >> memfree;
                std::cout << "MemFree: " << memfree << ")\n";

	}

     }
     return true;
    }
    

};
