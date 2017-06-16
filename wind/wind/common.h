#pragma once

#define ELEMENT_COUNT(arr) (sizeof(arr)/sizeof(*arr))

#define FUTURE_MARKET_DCE "DCE"
#define FUTURE_MARKET_SHF "SHF"
#define FUTURE_MARKET_CZC "CZC"
#define FUTURE_MARKET_CFE "CF"
#define SHANGHAI_MARKET_SH "SH"
#define SHENZHEN_MARKET_SZ "SZ"

#define DATA_DIRECTORY "E:/wind_data/"
#define FUTURE_K_MINUTE1BAR_DIRECTORY (string(DATA_DIRECTORY).append("future_kdata/"))
#define INDEX_K_MINUTE1BAR_DIRECTORY (string(DATA_DIRECTORY).append("index_kdata/"))
