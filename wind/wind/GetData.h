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

	enum PULLDATASTEP // ��ȡ���ݵ�ʱ���ȣ����£����ܻ��ǰ����ȡ��
	{
		MONTHLY, WEEKLY, DAILY
	};

	void GetKData(THANDLE hTdb, const char* szCode, const char* szMarket, int nBeginDate, int nEndDate, int nCycle, int nUserDef, int nCQFlag, int nAutoComplete);//������ֹ�����ڵ�k������
	void GetTickData(THANDLE hTdb, const char* szCode, const char* szMarket, int nDate);
	vector<string> get_code_list_from_csv(const string&  file_name);// ����csv�ļ����������ļ������к�Լ����
	string get_market_code_from_csv(const string & fname);// �����г����ʹ��룬��"SHF-1-0"
	string get_code_table(THANDLE hTdb, const string & fname, const string& market_string, int level);
	void get_kdata_from_code_table(THANDLE hTdb, const string& s, enum CYCTYPE cyc_type);
	void get_tick_data_from_code_table(THANDLE htdb, const string& code_table_file);

protected:
	void get_date_list_by_begin_and_end(date dbegin, date dend, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds);
	int virtual get_date_list(const string& codename, vector<int>& datelistbegin, vector<int>& datelistend, PULLDATASTEP pds) = 0;
	string data_dir_name;
};

