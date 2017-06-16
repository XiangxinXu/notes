#include "GetIndex.h"



GetIndex::GetIndex()
{
	data_dir_name = INDEX_K_MINUTE1BAR_DIRECTORY;
}


GetIndex::~GetIndex()
{
}

int GetIndex::get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds)
{
	date endpointer = date(2018, 1, 1);
	date startpointer = date(2011, 1, 1);
	get_date_list_by_begin_and_end(startpointer, endpointer, datelistbegin, datelistend, pds);
	return OK;
}


void GetIndex::GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate)
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
				float(pTickCopy.nBidAvPrice / 10000.) << pTickCopy.iTotalAskVolume << pTickCopy.iTotalBidVolume << pTickCopy.nIndex <<
				pTickCopy.nStocks << pTickCopy.nUps << pTickCopy.nDowns << pTickCopy.nHoldLines << NEWLINE;
		}
	}
	os.flush();
	os.close();

	//释放
	TDB_Free(pTick);

}