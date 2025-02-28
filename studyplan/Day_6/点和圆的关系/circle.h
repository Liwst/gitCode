#pragma once
#include<iostream>
#include "point.h"
using namespace std;
class Circle
{
public:
	//设置半径
	void set_R(int R);
	int get_R();
	//设置圆心
	void set_center(Point center);
	Point get_center();
private:
	int m_R;
	Point m_Center; // 圆心
};
