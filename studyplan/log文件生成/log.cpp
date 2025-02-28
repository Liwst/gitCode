#include<iostream>
#include<fstream>
#include<ctime>
#include<cstdlib>
using namespace std;


int main() {

	ofstream outfile("log.txt");
	if (!outfile) {
		cout << "文件创建失败" << endl;
		return 1;
	}
	srand(time(nullptr)); //初始化随机种子

	//生成基础时间戳
	long long timestamp = 1700000000000;


	for (int i = 0; i < 1000; i++) {
		//生成正确字符（A-Z）
		char correct = 'A' + (rand() % 26);

		//生成输入字符(80%正确，20%错误)

		char input;
		if (rand() % 100 < 80) {
			input = correct;
		}
		else {
			input = 'A' + (rand() % 26);
		}
		//写入文件
		outfile << correct << " " << input << " " << timestamp << endl;

		//生成下一个时间戳
		timestamp += rand() % 2000;
	}

	outfile.close();
	cout << "已生成log.txt，包含1000行符合题目要求的测试数据" << endl;
	return 0;
}