#include "GetFuture.h"
#include <exception>

GetFuture::GetFuture()
{
	data_dir_name = FUTURE_K_MINUTE1BAR_DIRECTORY;
}


GetFuture::~GetFuture()
{
}


int GetFuture::get_code_type(string s)
{
	string regstr1 = "([a-z]|[A-Z])+";
	string regstr2 = "([a-z]|[A-Z])+[0-9]{2}";
	string regstr3 = "([a-z]|[A-Z])+[0-9]{4}";
	string regstr4 = "([a-z]|[A-Z])+[0-9]{1}";
	boost::regex expression1(regstr1);
	boost::regex expression2(regstr2);
	boost::regex expression3(regstr3);
	boost::regex expression4(regstr4);
	
	if (boost::regex_match(s, expression1))
		return 1;
	if (boost::regex_match(s, expression2))
		return 2;
	if (boost::regex_match(s, expression3))
		return 3;
	if (boost::regex_match(s, expression4))
		return 4;
	return -1;
}

int GetFuture::get_date_list_from_4digits_codename(string s, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds)
{
	string ym = s.substr(s.size() - 4, 4);
	ym.append("01");
	if (ym.substr(0, 2) == string("99") || ym.substr(0, 2) == string("98") || ym.substr(0, 2) == string("97") || ym.substr(0, 2) == string("96"))
		ym = string("19").append(ym);
	else
		ym = string("20").append(ym);
	try
	{
		date endpointer = date(atoi(ym.substr(0, 4).c_str()), atoi(ym.substr(4, 2).c_str()), atoi(ym.substr(6, 2).c_str()));
		endpointer = month_forward(endpointer);
		date startpointer = year_backward(endpointer);
		startpointer = month_backward(startpointer);
		get_date_list_by_begin_and_end(startpointer, endpointer, datelistbegin, datelistend, pds);
	}
	catch (exception &e)
	{
		return INVALID_CODE_NAME;
	}
	
	return OK;
}

int GetFuture::get_date_list_from_continuously_codename(vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds)
{
	date endpointer = date(2018, 1, 1);
	date startpointer = date(2011, 1, 1);
	get_date_list_by_begin_and_end(startpointer, endpointer, datelistbegin, datelistend, pds);
	return OK;
}

int GetFuture::get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds)
{
	int t = get_code_type(codename);
	if (t == 1 || t == 2 || t == 4)
		if (get_date_list_from_continuously_codename(datelistbegin, datelistend, pds) != OK)
			return INVALID_CODE_NAME;
		else
			return OK;
	else if (t == 3)
		if (get_date_list_from_4digits_codename(codename, datelistbegin, datelistend, pds) != OK)
				return INVALID_CODE_NAME;
		else
			return OK;
	else
		return INVALID_CODE_NAME;
}

void GetFuture::GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate)
{
	//请求信息
	TDBDefine_ReqTick req = { 0 };
	strncpy_s(req.chCode, szCode, sizeof(req.chCode)); //代码写成你想获取的股票代码
	strncpy_s(req.chMarketKey, szMarket, sizeof(req.chMarketKey));
	req.nDate = nDate;
	req.nBeginTime = 0;
	req.nEndTime = 0;

	TDBDefine_Tick *pTick = NULL;
	int pCount = 0;
	int ret = TDB_GetTick(hTdb, &req, &pTick, &pCount);

	if (pCount == 0)
	{
		return;
	}
	string fname = string(szCode);
	fname.replace(fname.find("."), fname.size(), "_tick.csv");
	fname = string(data_dir_name).append(fname);
	csv::ofstream os(fname.c_str());
	os.set_delimiter(',', "$$");
	//os.enable_surround_quote_on_str(true, '\"');

	if (os.is_open())
	{
		for (int i = 0; i < pCount; ++i)
		{
			TDBDefine_Tick& pTickCopy = pTick[i];
			printf("万得代码 chWindCode:%s \n", pTickCopy.chCode);
			string dt = concat_date_time(pTickCopy.nDate, pTickCopy.nTime);
			//买卖盘字段
			std::string strAskPrice = array2str(pTickCopy.nAskPrice, ELEMENT_COUNT(pTickCopy.nAskPrice));
			std::string strAskVolume = array2str((const int*)pTickCopy.nAskVolume, ELEMENT_COUNT(pTickCopy.nAskVolume));
			std::string strBidPrice = array2str(pTickCopy.nBidPrice, ELEMENT_COUNT(pTickCopy.nBidPrice));
			std::string strBidVolume = array2str((const int*)pTickCopy.nBidVolume, ELEMENT_COUNT(pTickCopy.nBidVolume));
			if (dt.size() == 0)
				continue;
			os << pTickCopy.chCode << dt.c_str() << float(pTickCopy.nPrice / 10000.) << pTickCopy.iVolume << pTickCopy.iTurover << pTickCopy.nMatchItems
				<< pTickCopy.nInterest << pTickCopy.chTradeFlag << pTickCopy.chBSFlag << pTickCopy.iAccVolume << pTickCopy.iAccTurover <<
				float(pTickCopy.nHigh / 10000.) << float(pTickCopy.nLow / 10000.) << float(pTickCopy.nOpen / 10000.) << float(pTickCopy.nPreClose / 10000.) <<
				strAskPrice.c_str() << strAskVolume.c_str() << strBidPrice.c_str() << strBidVolume.c_str() << float(pTickCopy.nAskAvPrice / 10000.) <<
				float(pTickCopy.nBidAvPrice / 10000.) << pTickCopy.iTotalAskVolume << pTickCopy.iTotalBidVolume << pTickCopy.nSettle << pTickCopy.nPosition 
				<< pTickCopy.nCurDelta  << pTickCopy.nPreSettle << pTickCopy.nPrePosition << NEWLINE;
		}
	}
	os.flush();
	os.close();

	//释放
	TDB_Free(pTick);
	
}