//#include<iostream>
//using namespace std;
////stringµÄ¹¹Ôìº¯Êý
//
//void test01() {
//	string s1;
//	const char* str= "hello world";
//	
//	string s2(str);
//	cout << "s2 = " << s2 << endl;
//
//	string s3(s2);
//	cout << "s3 = " << s3 << endl;
//
//	string s4(10,'a');
//	cout << "s4 = " << s4 << endl;
//}
////string ¸³Öµ²Ù×÷
//void test02() {
//	string st1 = "heeo";
//
//	string st2 = st1;
//
//	string st3;
//	st3.assign("sdad");
//	cout << st3 << endl;
//
//	string st4;
//	st4.assign("gello g++", 4);
//	cout << st4 << endl;
//	string st5;
//	st5.append(st4, 0, 3);
//	cout << st5 << endl;
//}
//
////²éÕÒºÍÌæ»»
//void test03() {
//	string str1 = "abcdedefg";
//	int res = str1.find("de", 0);
//
//	if (res == -1) {
//		cout << " Î´ÕÒµ½×Ö·û´®" << endl;
//	}
//	else {
//		cout << "res = " << res << endl;
//	}
//	//rfind ´ÓÓÒÍù×óÕÒ
//	int res1 = str1.rfind("de", -1);
//	if (res1 == -1) {
//		cout << " Î´ÕÒµ½×Ö·û´®" << endl;
//	}
//	else {
//		cout << "res = " << res1 << endl;
//	}
//	//Ìæ»»
//	string str2 = "sfasgg";
//	str2.replace(1, 3, "1111");
//	cout << str2 << endl; //s1111gg
//
//	//×Ö·û´®±È½Ï
//
//	string num1 = "aello";
//	string num2 = "hello";
//	if (num1.compare(num2) == 0) {
//		cout << "num1 = num2" << endl;
//	}
//	else if (num1.compare(num2) > 0) {
//		cout << "num1 > num2" << endl;
//	}
//	else {
//		cout << "num1 < num2" << endl;
//	}
//
//	//×Ö·û´®½ØÈ¡
//	string test1 = "LILIJIAJIAHAOHAO";
//	string test2 = test1.substr(2, 5);
//	cout << test2 << endl;
//}
//int main() {
//	test03();
//	return 0;
//}