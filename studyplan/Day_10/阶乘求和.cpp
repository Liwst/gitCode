#include<iostream>
using namespace std;

long long fac(int n) {
	long long result = 1;

	for (int i = 2; i <= n; ++i) {
		result *= i;
	}
	return result;
}

int main() {
	long long num = 0;
	long long n;
	cin >> n;
	for (int i = 1; i <= n; ++i) {
		num += fac(i);
	}
	cout << num << endl;

	return 0;
}

