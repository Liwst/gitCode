#include<iostream>
#include<vector>
#include<algorithm>
using namespace std;

int main() {

	int n;
	cin >> n;
	int a[10] = { 1,0,0,0,1,0,1,0,2,1 };
	vector<pair<int, int>> x;
	for (int i = 0; i < n; ++i) {
		int b;
		cin >> b;
		int c = b, num = 0;
		while (c) {
			num += a[c % 10]; //每次都取一位数的余数，然后计算封闭个数
			c /= 10; //缩小一位数
		}	
		x.push_back({ num,b });

	}
	sort(x.begin(), x.end());
	for (int i = 0; i < n; ++i) {
		cout << x[i].second << " ";
		
	}
	return 0;
}
