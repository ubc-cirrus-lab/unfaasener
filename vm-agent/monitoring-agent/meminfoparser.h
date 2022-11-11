#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>

class meminfoparser
{

public:
    meminfoparser(size_t* results)
    {
        results[0] = 0; // total memory
        results[1] = 0; // available memory
    }
    bool get_meminfo(size_t* results) 
    {
        std::string token;
        std::ifstream meminfo("/proc/meminfo");
        std::string memtotal;
        std::string memfree;
        bool total_mem_read = false;
        bool avail_mem_read = false;
        while(meminfo >> token)
        {
            if ( token == "MemTotal:") {
                meminfo >> results[0];
                total_mem_read = true;
            }
            if ( token == "MemAvailable:" ) {
                meminfo >> results[1];
                avail_mem_read = true;
            }
            if ( (total_mem_read)&&(avail_mem_read) )
                break;
        }
        return true;
    }
    
};
