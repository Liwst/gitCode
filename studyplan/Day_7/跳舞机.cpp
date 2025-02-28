#include<iostream>
#include<vector>
#include<fstream>
#include<algorithm>
#include<sstream>
using namespace std;




int main() {
	vector<long> validTimes; // 存储所有正确敲击的时间戳

	// 读取文件并过滤有效记录

	ifstream file("log.txt");
	string line;

	while (getline(file, line)) {
		istringstream iss(line); //按行读取流式数据
		string correct, input;
		long long timestamp; //定义接受数据的变量

		if (iss >> correct >> input >> timestamp) {
			// 解析每行数据
			if (correct == input) {
				// 仅处理正确敲击的记录
				validTimes.push_back(timestamp);
			}
		}
	}

	// 考虑特殊记录的特殊情况
	if (validTimes.empty()) {
		cout << 0 << endl;
		return 0;
	}

	// 按时间戳排序确保正确
	sort(validTimes.begin(), validTimes.end());
	
	int maxK = 1, currentK = 1; // 初始至少为1次有效敲击
	for (size_t i = 1; i < validTimes.size(); ++i) {
		if (validTimes[i] - validTimes[i - 1] <= 1000) {
			// 满足连击条件
			currentK++;
			maxK = max( maxK, currentK );
		}
		else {
			currentK = 1; //重置当前连击计数
		}
	}

	cout << maxK << endl;
	return 0;
}