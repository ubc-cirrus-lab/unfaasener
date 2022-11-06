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
        cout << "Exp correctly thrown when buffer size is zero.\n";
        return 0;
    }
    cout << "Error: did not throw an exception for buffer size of zero.\n";
    return 1;
}

int test_const_zeros() {
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
    if (pred_result.prediction != 0.0) {
        std::cout << "Error: Predictor cannot predict constant zeros.";
        return 1;
    } else {
        std::cout << "Predictor predicted constant zeros.\n";
    }
    cpu_violation = pred_result.violation;
    return 0;
}

int main(void) {
    cout << "### Predictor tests ###\n";

    int test_results = 0; // 0 notifies passing tests

    test_results += test_buffer_size_check();
    test_results += test_const_zeros();

    if (test_results==0){
        cout << "=> OK - All " << tests_conducted << " tests passed!\n";
        return 0;
    } else {
        cout << "=> Failure - " << test_results << "/" << tests_conducted << " tests failed!\n";
        return 1;
    }
}