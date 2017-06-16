#pragma once

#include <boost/date_time.hpp>
#include <algorithm>
#include <assert.h>
#include "Windows.h"
#include "minicsv.h"

using namespace std;
using namespace boost::posix_time;
using namespace boost::gregorian;


date month_forward(date d);
date month_backward(date d);
date year_forward(date d);
date year_backward(date d);
date date_forward(date d);
date date_backward(date d);
date week_forward(date d);
date week_backward(date d);

string int2str(int n);
string lfill(const char c, int totallength, const std::string& s);
string concat_date_time(int date, int time);
std::string array2str(const int* arr, int len);