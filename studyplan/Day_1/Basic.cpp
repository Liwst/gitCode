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
//	cout << "����������������" << endl;
//	cin >> num1 >> num2;
//	cout << "���ǵĺ��ǣ�" << num1 + num2 << endl;
//	return 0;
//}

//#include <iostream>
//using namespace std;
//
//int main() {
//    int score;
//    cout << "�����뿼�Գɼ���";
//    cin >> score;
//
//    if (score >= 90) {
//        cout << "���㣡" << endl;
//    }
//    else if (score >= 60) {
//        cout << "�ϸ�" << endl;
//    }
//    else {
//        cout << "��ҪŬ��" << endl;
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
//	cout << "1-100�ĺ�Ϊ��" << sum << endl;
//
//	//forѭ����ӡ�˷���
//	for (int row = 1; row <= 9; row++) {
//		for (int j = 1; j <= row; j++) {
//			cout << j << "x" << row << "=" << j * row << "\t"; //ÿ�ζ���1��ʼ������j������ǰ��
//		}
//		cout << endl;
//	}
//	return 0;
//}
// ���׼�����
//

// BMIָ������
#include<iostream>
#include<cmath>
using namespace std;

int main() {
	double height, weight;
	cout << "������ߣ��ף���";
	cin >> height;
	cout << "�������أ������";
	cin >> weight;

	double bmi = weight / pow(height, 2);
	cout << "BMI:" << round(bmi * 10) / 10 << endl;

	if (bmi < 18.5)
		cout << "���ع���";
	else if (bmi < 24)
		cout << "������Χ";
	else
		cout << "����";

	return 0;
}