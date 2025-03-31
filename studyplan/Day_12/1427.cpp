#include<iostream>
#include<algorithm>
using namespace std;


int main(){
	int m,n;
	cin >> m >> n;
	int maxx,minn,result,constant=0;
	maxx = max(m,n);
	minn = min(m,n);
	for(int i = 1;;++i){
		int flag = 0;
		for(int j = 0; j*m <=i;j++){
			if((i-j*m)%n == 0){//另一个系数
			flag = 1;  //说明i可以被线性表示
			break;
		}
	}
	if(flag != 1){
		result = i;
		constant = 0;
	}
	else{
		constant++;
	}
	if(constant==minn){
		break;
	}
}
cout<<result;
	
	return 0;
}