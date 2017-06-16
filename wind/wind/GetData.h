#pragma once

#include "TDBAPI.h"
#include "common.h"
#include <conio.h>
#include "iostream"
#include <string>
#include "minicsv.h"
#include <vector>
#include <boost/regex.hpp>
#include <boost/date_time.hpp>
#include "utils.h"
#include "error_handle.h"



class GetData
{
public:
	GetData();
	virtual ~GetData();

	enum PULLDATASTEP // 获取数据的时间跨度，按月，按周还是按天获取。
	{
		MONTHLY, WEEKLY, DAILY
	};

	void GetKData(THANDLE hTdb, const char* szCode, const char* szMarket, int nBeginDate, int nEndDate, int nCycle, int nUserDef, int nCQFlag, int nAutoComplete);//返回起止日期内的k线数据
	void GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate);
	vector<string> get_code_list_from_csv(const string&  file_name);// 传入csv文件名，返回文件中所有合约代码
	string get_market_code_from_csv(const string & fname);// 返回市场类型代码，如"SHF-1-0"
	string get_code_table(THANDLE hTdb, const string & fname, const string& market_string, int level);
	void get_kdata_from_code_table(THANDLE hTdb, const string& s, enum CYCTYPE cyc_type);
	void get_tick_data_from_code_table(THANDLE htdb, const string& code_table_file);

protected:
	void get_date_list_by_begin_and_end(date dbegin, date dend, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);
	int virtual get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds) = 0;
	string data_dir_name;
};

