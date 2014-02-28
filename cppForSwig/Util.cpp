#include "Util.h"

#include <sstream>

using std::string;

namespace Util
{

string to_string(int val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(long val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(long long val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(unsigned val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(unsigned long val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(unsigned long long val)
{
   std::ostringstream ss;
   ss << val;
   return ss.str();
}
string to_string(float val)
{
   std::ostringstream ss;
   ss.precision(6);
   ss << val;
   return ss.str();
}
string to_string(double val)
{
   std::ostringstream ss;
   ss.precision(6);
   ss << val;
   return ss.str();
}
string to_string(long double val)
{
   std::ostringstream ss;
   ss.precision(6);
   ss << val;
   return ss.str();
}

}

// kate: indent-width 3; replace-tabs on;
