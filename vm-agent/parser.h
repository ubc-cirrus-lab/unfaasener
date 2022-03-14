#include <fstream>
#include <iostream>
#include <numeric>
#include <unistd.h>
#include <vector>
#include <memory>

class parser
{
//    size_t results[2];
public:
    parser(size_t* results)
    {
	results[0] = 0;
	results[1] = 0;
    }
    bool get_proc_stat_times(size_t* results) 
    {
     std::ifstream stat("/proc/stat");
     stat.ignore(5, ' ');
     std::vector<size_t> times;
     for (size_t time; stat >> time; times.push_back(time));
     if (times.size() < 4)
        return false;
     results[0] = times[3];
     results[1] = accumulate(times.begin(), times.end(), 0);
     return true;
    }
    

};
