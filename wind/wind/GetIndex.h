#pragma once
#include "GetData.h"
using namespace std;
using namespace boost::gregorian;


class GetIndex :
	public GetData
{
public:
	GetIndex();
	~GetIndex();
	int get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);
	void GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate);
};

