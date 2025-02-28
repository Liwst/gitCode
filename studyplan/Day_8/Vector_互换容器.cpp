//#include<iostream>
//#include<vector>
//using namespace std;
//
//
//void printVector(vector<int> &v) {
//	for (vector<int>::iterator it = v.begin(); it != v.end(); ++it) {
//		cout << *it << " ";
//	}
//	cout << endl;
//}
//void test01() {
//
//	vector<int> v1;
//	for (int i = 0; i < 10; ++i) {
//		v1.push_back(i);
//	}
//	cout << "交换前" << endl;
//	printVector(v1);
//
//	vector<int> v2;
//	for (int i = 10; i > 0; --i) {
//		v2.push_back(i);
//	}
//	printVector(v2);
//
//	cout << "交换后" << endl;
//	v1.swap(v2);
//	printVector(v1);
//	printVector(v2);
//}
//
//void test02() {
//	vector<int> v1;
//	for (int i = 0; i < 100000; ++i) {
//		v1.push_back(i);
//	}
//	cout << "V的容量为：" << v1.capacity() << endl;
//	cout << "V的大小为：" << v1.size() << endl;
//
//	v1.resize(3);
//
//	//巧用swap收缩内存
//	vector<int>(v1).swap(v1);
//	cout << "V的容量为：" << v1.capacity() << endl;
//	cout << "V的大小为：" << v1.size() << endl;
//}
//int main() {
//	// test01();
//
//	test02();
//
//	return 0;
//}