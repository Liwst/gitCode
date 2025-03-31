#include<iostream>
#include<string>

using namespace std;

int main() {
	int nn;
	cin >> nn;
	getchar();
	string s[10];
	for (int i = 0; i < nn; ++i) {
		getline(cin, s[i]);
	}
	for (int i = 0; i < nn; ++i) {
		cout << s[i] << endl << endl;
	}
	string v;
	
	while (getline(cin, v)) {
		for (int i = 0; i < v.length(); ++i) {
			if (v[i] != ' ') {
				cout << v[i];
			}
			else {
				cout << endl << endl;
			}
		}
		cout << endl << endl;
	}
	
	return 0;
}