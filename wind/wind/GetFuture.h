#pragma once

#include "GetData.h"
using namespace std;
using namespace boost::gregorian;

class GetFuture: public GetData
{
public:
	GetFuture();
	~GetFuture();

	int get_code_type(string s);// 返回期货代码类型：a    a00    a1701    icc1 分别对应类别 1 2 3 4, 其他为-1.
	int get_date_list_from_4digits_codename(string s, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);
	int get_date_list_from_continuously_codename(vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);

	void GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate);
private:
	int get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);
};

