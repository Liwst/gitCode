//#include<iostream>
//using namespace std;
//
//int main() {
//
//	int studentAge = 20;
//	double productPrice = 19.99;
//	string userName = "Alice";
//	cout << "Age:" << studentAge << endl;
//	cout << "Price: $" << productPrice << endl;
//	cout << "Name:" << userName << endl;
//	return 0;
//
//}

//#include<iostream>
//using namespace std;
//int main() {
//	int num1, num2;
//	cout << "请输入两个整数：" << endl;
//	cin >> num1 >> num2;
//	cout << "它们的和是：" << num1 + num2 << endl;
//	return 0;
//}

//#include <iostream>
//using namespace std;
//
//int main() {
//    int score;
//    cout << "请输入考试成绩：";
//    cin >> score;
//
//    if (score >= 90) {
//        cout << "优秀！" << endl;
//    }
//    else if (score >= 60) {
//        cout << "合格" << endl;
//    }
//    else {
//        cout << "需要努力" << endl;
//    }
//    return 0;
//}

//#include<iostream>
//using namespace std;
//int main() {
//	int sum = 0, i = 1;
//	while (i <= 100) {
//		sum += i;
//		i++;
//	}
//	cout << "1-100的和为：" << sum << endl;
//
//	//for循环打印乘法表
//	for (int row = 1; row <= 9; row++) {
//		for (int j = 1; j <= row; j++) {
//			cout << j << "x" << row << "=" << j * row << "\t"; //每次都从1开始，所以j变量在前面
//		}
//		cout << endl;
//	}
//	return 0;
//}
// 简易计算器
//

// BMI指数计算
#include<iostream>
#include<cmath>
using namespace std;

int main() {
	double height, weight;
	cout << "输入身高（米）：";
	cin >> height;
	cout << "输入体重（公斤）：";
	cin >> weight;

	double bmi = weight / pow(height, 2);
	cout << "BMI:" << round(bmi * 10) / 10 << endl;

	if (bmi < 18.5)
		cout << "体重过轻";
	else if (bmi < 24)
		cout << "正常范围";
	else
		cout << "超重";

	return 0;
}