#include<iostream>
#include<deque>

using namespace std;

void printDeque(const deque<int>& q) {
	for (deque<int>::const_iterator it = q.begin(); it != q.end(); ++it) {
		//*it = 100;
		cout << *it << " ";
	}
	cout << endl;
}
void test01() {

	deque<int> q1;
	for (int i = 0; i < 10; ++i) {
		q1.push_back(i);
	}
	deque<int> q2(q1.begin(), q1.end());

	deque<int> q3(10, 100);
	deque <int> q4(q3);
	printDeque(q1);
	printDeque(q2);
	printDeque(q3);
	printDeque(q4);
}

int main() {

	test01();
	return 0;
}