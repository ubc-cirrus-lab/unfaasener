#include <fstream>
#include <iostream>


class procstatparser
{

public:
    procstatparser(size_t* results)
    {
        results[0] = 0;
        results[1] = 0;
    }
    bool get_proc_stat_times(size_t* results) 
    {
        std::ifstream stat("/proc/stat");
        stat.ignore(5, ' ');
        results[0] = 0;
        results[1] = 0;
        size_t time;
        for (int i=0; i<4; i++) {
            stat >> time;
            results[1] += time;
            if (i==3)
                results[0] += time;
        }
        return true;
    }

};
