//#include <iostream>
//#include <algorithm> // 用于std::min
//
//using namespace std;
//
//long long compute(long long N) {
//    long long count = 0;
//
//    // 处理i < 10的情况
//    long long lower_limit = min(N, 9LL);
//    for (long long i = 1; i <= lower_limit; ++i) {
//        long long A = i * (i + 1) / 2;
//        long long B = 1;
//        for (long long j = 2; j <= i; ++j) {
//            B *= j;
//        }
//        if ((A - B) % 100 == 0) {
//            ++count;
//        }
//    }
//
//    if (N < 10) {
//        return count;
//    }
//
//    // 处理i >= 10的情况
//    long long case1 = N / 200;
//
//    long long case2 = (N >= 24) ? ((N - 24) / 200 + 1) : 0;
//    long long case3 = (N >= 175) ? ((N - 175) / 200 + 1) : 0;
//    long long case4 = (N >= 199) ? ((N - 199) / 200 + 1) : 0;
//
//    count += case1 + case2 + case3 + case4;
//
//    return count;
//}
//
//int main() {
//    long long N = 2024041331404202;
//    cout << compute(N) << endl;
//    return 0;
//}