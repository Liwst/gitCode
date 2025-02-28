#include<iostream>
using namespace std;



class Cube
{
public:
	void set_m_L(int L) {
		m_L = L;
	}

	int get_m_L() {
		return m_L;
	}
	void set_m_W(int W) {
		m_W = W;
	}

	int get_m_W() {
		return m_W;
	}
	void set_m_H(int H) {
		m_H = H;
	}

	int get_m_H() {
		return m_H;
	}

	int calculateS() {
		return 2 * m_L * m_W + 2 * m_L * m_H + 2 * m_H * m_W;
	}
	int calculateV() {
		return m_L * m_H * m_W;
	}

	//利用成员函数判断两个立方体是否相等
	bool isSameByClass(Cube& c) {
		if (m_H == c.get_m_H() && m_L == c.get_m_L() && m_W == c.get_m_W()) {
			return true;
		}
		return false;
	}
private:
	int m_L;
	int m_W;
	int m_H;

};

//利用全局函数判断 两个立方体是否相等
bool isSame(Cube& c1, Cube& c2) {
	if (c1.get_m_H() == c2.get_m_H() && c2.get_m_L() == c1.get_m_L() && c1.get_m_W() == c2.get_m_W()) {
		return true;
	}
	return false;
}
int main() {

	Cube c1;
	c1.set_m_L(10);
	c1.set_m_H(10);
	c1.set_m_W(10);
	
	cout << "c1的面积为：" << c1.calculateS() << endl;
	cout << "c1的体积为：" << c1.calculateV() << endl;

	Cube c2;
	c2.set_m_L(5);
	c2.set_m_H(5);
	c2.set_m_W(5);

	cout << "c1的面积为：" << c2.calculateS() << endl;
	cout << "c1的体积为：" << c2.calculateV() << endl;
	//全局函数判断
	bool ret = isSame(c1, c2);
	if (ret) {
		cout << "c1和c2是相等的" << endl;

	}
	else
	{
		cout << "c1和c2是不相等的" << endl;
	}

	//成员函数判断
	bool res = c1.isSameByClass(c2);

	if (res) {
		cout << "c1和c2是相等的" << endl;

	}
	else
	{
		cout << "c1和c2是不相等的" << endl;
	}
	return 0;
}