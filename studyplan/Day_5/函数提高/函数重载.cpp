#include<iostream>
using namespace std;

// 函数重载的注意事项
//1、引用作为重载的条件
void func(int &a) {
	cout << "func(int &a)的调用" << endl;

}
void func(const int &a) {
	cout << "func(const int &a)的调用" << endl;

}
//2、函数重载碰到默认参数
void func2(int a, int b) {
	cout << "func2(int a)的调用" << endl;

}
void func2(int a) {
	cout << "func2(int a)的调用" << endl;

}
int main() {
	/*const int a = 10;
	func(a);
	func(20);*/
	func2(10);
	system("pause");
	return 0;
}