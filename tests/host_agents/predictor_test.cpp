#include <ring.h>
#include <predictor.h>

using namespace std;

int tests_conducted = 0;

int test_buffer_size_check() {
    tests_conducted ++;
    size_t ring_size = 0;
    ring cpu_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    double cpu_pred_old = 0;
    size_t cpu_violation;
    try {
        auto pred_result = cpu_predictor.compute_predicton_ExponentialMovingAverage(cpu_pred_old, 0, 1);
    } catch(std::exception &e) {
        cout << "Exp correctly thrown by EMA predictor when buffer size is zero.\n";
        return 0;
    }
    cout << "Error: did not throw an exception for buffer size of zero.\n";
    return 1;
}

int test_const_zeros_ema() {
    tests_conducted ++;
    size_t ring_size = 5;
    ring cpu_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    double cpu_pred_old = 0;
    size_t cpu_violation;
    auto pred_result = cpu_predictor.compute_predicton_ExponentialMovingAverage(cpu_pred_old, 0, 1);
    std::cout << "Predicted Value with zero trace (EMA): " << pred_result.prediction << "\n";
    cpu_violation = pred_result.violation;
    return 0;
}

int test_const_zeros_mc() {
    tests_conducted ++;
    size_t ring_size = 5;
    ring cpu_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    cpu_utilization_buffer.push(double(0.0));
    double cpu_pred_old = 0;
    size_t cpu_violation;
    auto pred_result = cpu_predictor.compute_predicton_MarkovChain(cpu_pred_old, 0, 1);
    std::cout << "Predicted Value with zero trace (MC): " << pred_result.prediction << "\n";
    return 0;
}

int test_trace1_ema() {
    tests_conducted ++;
    size_t ring_size = 5;
    ring cpu_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    std::cout << "EMA prdictions [0-10-0-10 trace]: \n";
    
    double cpu_pred_old = 0;
    size_t cpu_violation;

    cpu_utilization_buffer.push(double(0));
    auto pred_result = cpu_predictor.compute_predicton_ExponentialMovingAverage(cpu_pred_old, 0, 1);
    std::cout << "Real: 10, Pred: " << pred_result.prediction << "\n";
    cpu_pred_old = pred_result.prediction;

    for (int i=0; i<10; i++){
        cpu_utilization_buffer.push(double(10));
        pred_result = cpu_predictor.compute_predicton_ExponentialMovingAverage(cpu_pred_old, 0, 1);
        std::cout << "Real: 0, Pred: " << pred_result.prediction << "\n";
        cpu_pred_old = pred_result.prediction;
        cpu_utilization_buffer.push(double(0));
        pred_result = cpu_predictor.compute_predicton_ExponentialMovingAverage(cpu_pred_old, 0, 1);
        std::cout << "Real: 10, Pred: " << pred_result.prediction << "\n";
        cpu_pred_old = pred_result.prediction;
    }
    
    return 0;
}


int test_trace1_mc() {
    tests_conducted ++;
    size_t ring_size = 5;
    ring cpu_utilization_buffer(ring_size);
    predictor cpu_predictor(&cpu_utilization_buffer);
    std::cout << "MC prdictions [0-10-0-10 trace]: \n";
    
    double cpu_pred_old = 0;
    size_t cpu_violation;

    cpu_utilization_buffer.push(double(0));
    auto pred_result = cpu_predictor.compute_predicton_MarkovChain(cpu_pred_old, 0, 1);
    std::cout << "Recent:0, Future:10, Pred:" << pred_result.prediction << "\n";
    cpu_pred_old = pred_result.prediction;

    for (int i=0; i<10; i++){
        cpu_utilization_buffer.push(double(10));
        pred_result = cpu_predictor.compute_predicton_MarkovChain(cpu_pred_old, 0, 1);
        std::cout << "Recent:10, Future:0, Pred:" << pred_result.prediction << "\n";
        cpu_pred_old = pred_result.prediction;
        cpu_utilization_buffer.push(double(0));
        pred_result = cpu_predictor.compute_predicton_MarkovChain(cpu_pred_old, 0, 1);
        std::cout << "Recent:0, Future:10, Pred:" << pred_result.prediction << "\n";
        cpu_pred_old = pred_result.prediction;
    }
    
    return 0;
}


int main(void) {
    cout << "### Predictor tests ###\n";

    int test_results = 0; // 0 notifies passing tests

    test_results += test_buffer_size_check();
    test_results += test_const_zeros_ema();
    test_results += test_const_zeros_mc();
    test_results += test_trace1_ema();
    test_results += test_trace1_mc();

    if (test_results == 0){
        cout << "=> OK - All " << tests_conducted << " tests passed!\n";
        return 0;
    } else {
        cout << "=> Failure - " << test_results << "/" << tests_conducted << " tests failed!\n";
        return 1;
    }
}