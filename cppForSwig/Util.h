#ifndef _UTIL_H
#define _UTIL_H

#include <string>

// Simulate C++11: http://www.cplusplus.com/reference/string/to_string/
namespace Util
{

std::string to_string(int val);
std::string to_string(long val);
std::string to_string(long long val);
std::string to_string(unsigned val);
std::string to_string(unsigned long val);
std::string to_string(unsigned long long val);
std::string to_string(float val);
std::string to_string(double val);
std::string to_string(long double val);
}

#endif

// kate: indent-width 3; replace-tabs on;
