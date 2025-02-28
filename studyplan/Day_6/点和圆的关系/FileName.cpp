#include<iostream>
using namespace std;
#include"circle.h"
#include"point.h"
//class Point
//{
//public:
//	void set_X(int X) {
//		m_X = X;
//	}
//	int get_X() {
//		return m_X;
//	}
//	void set_Y(int Y) {
//		m_Y = Y;
//	}
//	int get_Y() {
//		return m_Y;
//	}
//private:
//	int m_X;
//	int m_Y;
//};
//class Circle
//{
//public:
//	//设置半径
//	void set_R(int R) {
//		m_R = R;
//	}
//	int get_R() {
//		return m_R;
//	}
//	//设置圆心
//	void set_center(Point center) {
//		m_Center = center;
//
//	}
//	Point get_center() {
//		return m_Center;
//	}
//private:
//	int m_R;
//	Point m_Center; // 圆心
//};

//判断点和圆的关系
void isInCircle(Circle &c, Point& p)
{
	//计算两点之间距离的平方
	int distance = (c.get_center().get_X() - p.get_X())* (c.get_center().get_X() - p.get_X()) +
		(c.get_center().get_Y() - p.get_Y()) * (c.get_center().get_Y() - p.get_Y());
	//计算半径的平方
	int rD = c.get_R() * c.get_R();

	if (distance == rD) {
		cout << "点在圆上" << endl;
	}
	else if (distance < rD) {
		cout << "点在圆内" << endl;
	}
	else {
		cout << "点在圆外" << endl;
	

	}
}

int main() {
	//创建圆
	Circle c;
	c.set_R(10);
	Point center;
	center.set_X(10);
	center.set_Y(0);
	c.set_center(center);
	//创建点
	Point p;
	p.set_X(10);
	p.set_Y(100);
	isInCircle(c,p);

	return 0;
}