#include "utils.h"
#include "error_handle.h"

std::string int2str(int n)
{
	char szBuf[32];
	_snprintf_s(szBuf, sizeof(szBuf) / sizeof(szBuf[0]), "%d", n);
	return std::string(szBuf);
}

std::string array2str(const int* arr, int len)
{
	std::string str;
	for (int i = 0; i < len; i++)
	{
		if (i == len - 1)
		{
			str += int2str(arr[i]) + " ";
		}
		else
		{
			str += int2str(arr[i]) + ",";
		}
	}
	return str;
}

std::string lfill(const char c, int totallength, const std::string& s)
{
	if (s.size() >= totallength)
	{
		return s;
	}
	else {
		unsigned int csize = totallength - s.size();
		std::string apc(csize, c);
		return apc.append(s);
	}
}

ptime time_parse_exact(const string& time_str, const string& format)
{
	ptime output;
	time_input_facet facet1(format, 1);

	std::stringstream ss1(time_str);
	ss1.imbue(std::locale(ss1.getloc(), &facet1));
	ss1 >> output;

	return output;
}


std::string standardize_date_time(const std::string& date, const std::string& time)
{
	std::string t = time;
	if (time.size() >= 8)
	{
		t = time.substr(0, 7);
	}
	std::string dt = date + time;
	ptime pt = time_parse_exact(dt, "%Y%m%d%H%M%S");
	return to_simple_string(pt);
}

boost::gregorian::date month_forward(date d)
{
	month_iterator miter(d);
	++miter;
	return date(miter->year_month_day());
}

boost::gregorian::date month_backward(date d)
{
	month_iterator miter(d);
	--miter;
	return date(miter->year_month_day());
}

boost::gregorian::date year_forward(date d)
{
	year_iterator miter(d);
	++miter;
	return date(miter->year_month_day());
}

boost::gregorian::date year_backward(date d)
{
	year_iterator miter(d);
	--miter;
	return date(miter->year_month_day());
}

boost::gregorian::date date_forward(date d)
{
	day_iterator miter(d);
	++miter;
	return date(miter->year_month_day());
}

boost::gregorian::date date_backward(date d)
{
	day_iterator miter(d);
	--miter;
	return date(miter->year_month_day());
}

boost::gregorian::date week_forward(date d)
{
	week_iterator witer(d);
	++witer;
	return date(witer->year_month_day());
}

boost::gregorian::date week_backward(date d)
{
	week_iterator witer(d);
	--witer;
	return date(witer->year_month_day());
}

// ����int��20010101(YYYYMMDD)��date��int��093001000(HHMMSS+3λ����)��time
string concat_date_time(int date, int time)
{
	if (date == 0 || time == 0)
		return string("");
	std::string d = int2str(date);
	d.replace(6, 0, "-");
	d.replace(4, 0, "-");
	std::string t = int2str(time);
	t = lfill('0', 9, t);
	t = t.substr(0, 6);
	t.replace(4, 0, ":");
	t.replace(2, 0, ":");
	t.replace(0, 0, " ");
	return d.append(t);
}

void print_error_msg(TDB_ERROR err)
{
	switch (err)
	{
	case TDB_SUCCESS:
		printf_s("�ɹ���");
	case TDB_NETWORK_ERROR:
		printf_s("�������");
	case TDB_NETWORK_TIMEOUT:
		printf_s("���糬ʱ��");
	case TDB_NO_DATA:
		printf_s("û�����ݡ�");
	case TDB_OUT_OF_MEMORY:
		printf_s("�ڴ�ľ���");
	case TDB_LOGIN_FAILED:
		printf_s("��½ʧ�ܡ�");
	case TDB_INVALID_CODE_TYPE:
		printf_s("��Ч�Ĵ������͡�");
	case TDB_INVALID_PARAMS:
		printf_s("��Ч�Ĳ�����");
	case TDB_WRONG_FORMULA:
		printf_s("ָ�깫ʽ����");
	default:
		break;
	}
}
