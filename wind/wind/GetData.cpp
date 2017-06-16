#include "GetData.h"
#include <io.h>

GetData::GetData()
{
}


GetData::~GetData()
{
}

void GetData::GetKData(THANDLE hTdb, const char* szCode, const char* szMarket, int nBeginDate, int nEndDate, int nCycle, int nUserDef, int nCQFlag, int nAutoComplete)
{
	//请求K线
	TDBDefine_ReqKLine* req = new TDBDefine_ReqKLine;
	strncpy_s(req->chCode, szCode, ELEMENT_COUNT(req->chCode));
	strncpy_s(req->chMarketKey, szMarket, ELEMENT_COUNT(req->chMarketKey));

	req->nCQFlag = REFILL_BACKWARD/*(REFILLFLAG)nCQFlag*/;//除权标志，由用户定义
	req->nBeginDate = nBeginDate;//开始日期
	req->nEndDate = nEndDate;//结束日期
	req->nBeginTime = 0;//开始时间
	req->nEndTime = 235959000;//结束时间
	req->nAutoComplete = nAutoComplete;//自动补齐
	req->nCycType = (CYCTYPE)nCycle;
	req->nCycDef = 1;

	//返回结构体指针
	TDBDefine_KLine* kLine = NULL;
	//返回数
	int pCount = 0;
	//API请求K线
	TDB_GetKLine(hTdb, req, &kLine, &pCount);
	delete req;
	req = NULL;

	if (pCount == 0)
	{
		return;
	}
	string fname = string(szCode);
	fname.replace(fname.find("."), fname.size(), ".csv");
	fname = string(data_dir_name).append(fname);
	csv::ofstream os(fname.c_str());
	os.set_delimiter(',', "$$");
	//os.enable_surround_quote_on_str(true, '\"');

	if (os.is_open())
	{
		for (int i = 0; i < pCount; ++i)
		{
			string dt = concat_date_time(kLine[i].nDate, kLine[i].nTime);
			if (dt.size() == 0)
				continue;
// 			os << kLine[i].chCode << dt.c_str() << float(kLine[i].nOpen / 10000.) << float(kLine[i].nHigh / 10000.) << float(kLine[i].nLow / 10000.) << float(kLine[i].nClose / 10000.) <<
// 				kLine[i].iVolume << kLine[i].iTurover << kLine[i].nMatchItems << kLine[i].nInterest << NEWLINE;
			os << dt.c_str()<< float(kLine[i].nClose / 10000.) <<kLine[i].iVolume<< kLine[i].nInterest << NEWLINE;


		}
	}
	os.flush();
	os.close();
	TDB_Free(kLine);
}

void GetData::GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate) 
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
			os << pTickCopy.chCode << dt.c_str() << float(pTickCopy.nPrice/ 10000.) << pTickCopy.iVolume << pTickCopy.iTurover << pTickCopy.nMatchItems
				<< pTickCopy.nInterest << pTickCopy.chTradeFlag << pTickCopy.chBSFlag << pTickCopy.iAccVolume << pTickCopy.iAccTurover <<
				float(pTickCopy.nHigh / 10000.) << float(pTickCopy.nLow / 10000.) << float(pTickCopy.nOpen / 10000.) << float(pTickCopy.nPreClose / 10000.) <<
				strAskPrice.c_str() << strAskVolume.c_str() << strBidPrice.c_str() << strBidVolume.c_str() << float(pTickCopy.nAskAvPrice/ 10000.) <<
				float(pTickCopy.nBidAvPrice / 10000.) << pTickCopy.iTotalAskVolume<< pTickCopy.iTotalBidVolume<< NEWLINE;
		}
	}
	os.flush();
	os.close();

	//释放
	TDB_Free(pTick);

}

std::vector<std::string> GetData::get_code_list_from_csv(const string& file_name)
{
	csv::ifstream is(file_name.c_str());
	is.set_delimiter(',', "$$");

	vector<string> res;
	string nul;
	if (is.is_open())
	{
		int count = 0;
		while (is.read_line())
		{
			is >> nul;
			res.push_back(nul);
			std::cout << res[res.size() - 1] << std::endl;
		}
		is.close();
	}
	return res;
}


std::string GetData::get_market_code_from_csv(const string & fname)
{
	csv::ifstream is(fname.c_str());
	is.set_delimiter(',', "$$");

	string nul, market_code;
	if (is.is_open())
	{
		is.read_line();
		is >> nul >> market_code;
		is.close();
	}
	return market_code;
}

void GetData::get_date_list_by_begin_and_end(date startpointer, date endpointer, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds)
{
	date(*func)(date) = NULL;
	switch (pds)
	{
	case GetData::MONTHLY:
		func = month_forward;
		break;
	case GetData::WEEKLY:
		func = week_forward;
		break;
	case GetData::DAILY:
		func = date_forward;
		break;
	default:
		break;
	}
	if (func == NULL)
		return;
	for (; startpointer < endpointer; startpointer = func(startpointer))
	{
		int y = startpointer.year() * 10000;
		int m = startpointer.month() * 100;
		int d = startpointer.day();
		datelistbegin.push_back(y + m + d);
		date stependpointer = func(startpointer);
		stependpointer = date_backward(stependpointer);
		y = stependpointer.year() * 10000;
		m = stependpointer.month() * 100;
		d = stependpointer.day();
		datelistend.push_back(y + m + d);
	}
}


string GetData::get_code_table(THANDLE hTdb, const string & fname, const string& market_string, int level)
{
	string mktstring(market_string);
	char lev_char[2];
	sprintf_s(lev_char, "%d", level);
	string level_str = string(lev_char);
	mktstring.append("-").append(level_str).append("-0");
	const char* szMarket = mktstring.c_str();
	int pcount = 0;
	TDBDefine_Code* pData;
	string file_name = string(market_string).append(fname);
	file_name = string(DATA_DIRECTORY).append(file_name);
	if ((_access(file_name.c_str(), 0)) != -1)
		return file_name;

	int res = TDB_GetCodeTable(hTdb, szMarket, &pData, &pcount);
	if (res == TDB_SUCCESS)
	{
		csv::ofstream os(file_name.c_str());
		os.set_delimiter(',', "$$");

		if (os.is_open())
		{
			for (int i = 0; i < pcount; ++i)
			{
				os << pData[i].chCode << pData[i].chMarket << pData[i].chENName << pData[i].chENName << pData[i].nType << NEWLINE;
			}
			os.flush();
			os.close();
		}
		TDB_Free(pData);
		return file_name;
	}
	else
	{
		print_error_msg((TDB_ERROR)res);
		TDB_Free(pData);
		return string("");
	}
}

void GetData::get_kdata_from_code_table(THANDLE hTdb, const string& code_table_file, enum CYCTYPE cyc_type)
{
	vector<string> code_list = get_code_list_from_csv(code_table_file);
	string market_code = get_market_code_from_csv(code_table_file);
	int pos_ = market_code.find_first_of('-');
	string code_suffix = market_code.substr(0, pos_);
	code_suffix = string(".").append(code_suffix);

	PULLDATASTEP pds;
	// 秒和tickbar一次取一周的数据，其他一次取一个月数据。
	if (cyc_type == CYC_SECOND || cyc_type == CYC_TICKBAR)
		pds = WEEKLY;
	else
		pds = MONTHLY;

	for (vector<string>::iterator it = code_list.begin(); it != code_list.end(); ++it)
	{
		vector<int> datelistbegin;
		vector<int> datelistend;
		
		if (get_date_list(*it, datelistbegin, datelistend, pds) != OK)
			continue;
		
		string codenamestr = *it;
		if (!(codenamestr.substr(0, 2) == string("T1")|| codenamestr.substr(0, 3) == string("TF1")))
			continue;
		codenamestr = codenamestr.append(code_suffix);
		for (vector<int>::const_iterator bit = datelistbegin.begin(), eit = datelistend.begin(); bit != datelistbegin.end() && eit != datelistend.end(); ++bit, ++eit)
		{
			GetKData(hTdb, codenamestr.c_str(), market_code.c_str(), *bit, *eit, cyc_type, 0, 0, 1);
		}
	}
}

void GetData::get_tick_data_from_code_table(THANDLE hTdb, const string& code_table_file)
{
	vector<string> code_list = get_code_list_from_csv(code_table_file);
	string market_code = get_market_code_from_csv(code_table_file);
	int pos_ = market_code.find_first_of('-');
	string code_suffix = market_code.substr(0, pos_);
	code_suffix = string(".").append(code_suffix);

	PULLDATASTEP pds = DAILY;
	for (vector<string>::iterator it = code_list.begin(); it != code_list.end(); ++it)
	{
		vector<int> datelistbegin;
		vector<int> datelistend;

		if (get_date_list(*it, datelistbegin, datelistend, pds) != OK)
			continue;

		string codenamestr = *it;
		if (!(codenamestr.substr(0, 2) == string("cu1703")))
			continue;
		codenamestr = codenamestr.append(code_suffix);
		for (vector<int>::const_iterator bit = datelistbegin.begin(), eit = datelistend.begin(); bit != datelistbegin.end() && eit != datelistend.end(); ++bit, ++eit)
		{
			GetTickData(hTdb, codenamestr.c_str(), market_code.c_str(), *bit);
		}
	}
}
