//#include<iostream>
//using namespace std;
//
//// 辗转相除求最大公约数
//
//int main() {
//	int m, n;
//	cin >> m >> n;
//	int x = m, y = n;
//	int b = x % y;
//	while (b != 0) {
//		x = y;
//		y = b;
//		b = x % y;
//	}
//	//此时y就是想要的最大公约数
//	cout << y << " "<< m *n /y;  //最小公倍数 = 两数相乘/最大公约数
//	return 0;
//}