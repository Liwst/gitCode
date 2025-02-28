#pragma once
#include<iostream>
using namespace std;
class Point
{
public:
	void set_X(int X);
	int get_X();
	void set_Y(int Y);
	int get_Y();
private:
	int m_X;
	int m_Y;
};