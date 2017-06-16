#pragma once

#include "GetFuture.h"
#include "GetIndex.h"
#include "TDBAPI.h"

int main()
{
	THANDLE hTdb = NULL;
	char* svr_ip = "114.80.154.34";
	int svr_port = 6261;
	char* username = "TD1080308004";
	char* password = "38525748";
	int level = 2;
	string market_string(FUTURE_MARKET_CFE);
	string code_table_file = string("code_table.csv");

	TDBDefine_ResLogin LoginRes = { 0 };

	//设置服务器信息
	OPEN_SETTINGS settings = { 0 };
	strcpy_s(settings.szIP, svr_ip);
	sprintf_s(settings.szPort, "%d", svr_port);
	strcpy_s(settings.szUser, username);
	strcpy_s(settings.szPassword, password);
	settings.nRetryCount = 100;
	settings.nRetryGap = 100;
	settings.nTimeOutVal = 100;

	//TDB_Open
	hTdb = TDB_Open(&settings, &LoginRes);

	int nRet = TDB_SUCCESS;

	if (!hTdb)
	{
		printf("连接失败！");
		getchar();
		return 0;
	}

	GetFuture get_data;
	/*GetIndex get_data;*/
	code_table_file = get_data.get_code_table(hTdb, code_table_file, market_string, level);
	if (code_table_file != "")
		get_data.get_kdata_from_code_table(hTdb, code_table_file, CYC_SECOND);
		//get_data.get_tick_data_from_code_table(hTdb, code_table_file);

	printf("输入任意键结束程序");
	getchar();
	if (hTdb)
		nRet = TDB_Close(hTdb);

	return 0;
}
