#include <vector>
#include <stdexcept>
#include <cmath>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <iostream>
#include <fstream>

using namespace std;

#define MC_STM_STATE_COUNT 27
#define LOGGING 0

class predictor
{
    ring* utilization_records;
    double sum = 0.0;
    double max_util, prediction = 0.0;
    double alpha = 0.85;
    double ema_margin = 0.2;
    double violation_margin = 0.2;
    int size;
    // tje following variables are for the Markiv Chain predictor
    double mc_margin = 0.05;
    double mc_res_margin = 1;
    double mc_util_res = 4; // 4%
    // state_count = int(100 / util_res) + 2
    double stm[MC_STM_STATE_COUNT][MC_STM_STATE_COUNT]; // state transition matrix
    unsigned short row_empty[MC_STM_STATE_COUNT];
    unsigned short past_state = 0;
    unsigned short new_state;
    
public:
    predictor(ring* buffer)
    {
        utilization_records = buffer;
	    sum = 0;
        for (int i=0; i<MC_STM_STATE_COUNT; i++){
            row_empty[i] = 1;
            for (int j=0; j<MC_STM_STATE_COUNT; j++){
                stm[i][j] = 0;
            }
        }
    }
    
    auto compute_predicton_ExponentialMovingAverage(double old_value, int type, int initialFlag)
    {
        // type: 0 -> cpu, 1 -> memory
        size_t violation = 0;
        max_util = 0;
        size = utilization_records->size();
        if (size == 0)
            throw std::logic_error( "Exception: record buffer has size 0!" );
        int i = 0;
        double records[size];
        while (i < size)
        {
            records[i] = utilization_records->pop();
            i++;
        }
        // calculate the max for the records array
        for(i = 0; i < size; ++i) {
            if (records[i] > max_util)
            {
                max_util = records[i];
            }
        }
        prediction = (alpha *  max_util  + (1-alpha)*old_value ) * (1+ema_margin);
        if ( prediction > 100)
            prediction = 100;
        if ( (int(max_util) - int(old_value) > 100*violation_margin ) || (int(old_value) - int(max_util) > 100*violation_margin ) || (prediction > old_value + 100*violation_margin)|| (prediction + 100 *violation_margin < old_value ) || (initialFlag == 1))
            violation = 1;
        struct result {double prediction; size_t violation;};
        return result {prediction, violation};
    }

    auto compute_predicton_MarkovChain(double old_value, int type, int initialFlag)
    {
        // type: 0 -> cpu, 1 -> memory
        size_t violation = 0;

        size = utilization_records->size();
        if (size == 0)
            throw std::logic_error( "Exception: record buffer has size 0!" );
        int i = 0;
        double records[size];
        while (i < size)
        {
            records[i] = utilization_records->pop();
            i++;
        }
        // calculate the max utilization of the records array
        max_util = 0;
        for(i = 0; i < size; ++i) {
            if (records[i] > max_util)
            {
                if (records[i] > 100){
                    max_util = 100;
                } else if (records[i] < 0) {
                    max_util = 0;
                } else {
                    max_util = records[i];
                }
            }
        }
        
        new_state = (unsigned short) round(max_util/mc_util_res);
        stm[past_state][new_state] += 1;
        if (row_empty[past_state]==1)
            row_empty[past_state] = 0;
        past_state = new_state;
        double ema_prediction = (alpha *  max_util  + (1-alpha)*old_value ) * (1+ema_margin);
        if (row_empty[new_state]==1) {
            std::cout << "EMA used \n";
            prediction = ema_prediction;
        } else {
            if (LOGGING){
                std::cout << "STD used \n";
                std::cout << "new state: " << new_state << " with STM row content: ";
                for (int i=0; i<MC_STM_STATE_COUNT; i++){
                    std::cout << stm[new_state][i]<<", ";
                }
                std::cout << "\n";
            }
            double row_sum = 0;
            for (int i=0; i<MC_STM_STATE_COUNT; i++){
                prediction += mc_util_res*(i+mc_res_margin)*stm[new_state][i];
                row_sum += stm[new_state][i];
            }
            prediction = prediction/row_sum;
            prediction = prediction*(1+mc_margin);
        }
        if (prediction > 100)
            prediction = 100;

        if ( (int(max_util) - int(old_value) > 100*violation_margin ) || (int(old_value) - int(max_util) > 100*violation_margin ) || (prediction > old_value + 100*violation_margin)|| (prediction + 100 *violation_margin < old_value ) || (initialFlag == 1))
            violation = 1;
        
        struct result {double prediction; size_t violation;};
        return result {prediction, violation};
    }
};
