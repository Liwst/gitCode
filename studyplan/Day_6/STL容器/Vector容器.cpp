#include<iostream>
#include<vector>
using namespace std;

void printVector(vector<int> &v) {
	for (vector<int>::iterator it = v.begin(); it != v.end(); it++) {
		cout << (*it) << " ";
	}
	cout << endl;
}
void test01() {
	vector<int> v1;

	for (int i = 0; i < 10; i++) {
		v1.push_back(1);
	}
	printVector(v1);

	vector<int>v2(v1.begin(), v1.end());
	printVector(v2);

	vector<int>v3(10, 100);
	printVector(v3);

	vector<int>v4(v3);
	printVector(v4);
}
void test02() {

	vector<int> v1;
	for (int i = 0; i < 10; i++) {
		v1.push_back(i);

	}
	vector<int>v2;
	//v2 = v1;
	v2.assign(v1.begin(), v1.end());
	printVector(v2);
}



int main() {
	test02();
	return 0;
}