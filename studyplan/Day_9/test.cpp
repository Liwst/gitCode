#include<iostream>
using namespace std;
#include<iomanip>

int main(){
	
	
	double F;
	double c;
	cin >> F;
	c = 5*(F-32)/9;
	cout << fixed<<setprecision(2)<<"c="<<c;
	
	return 0;
}