////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _H_JSONCODEC_
#define _H_JSONCODEC_

using namespace std;

#include <stdexcept>
#include <memory>
#include <vector>
#include <string>
#include <map>
#include <sstream>

#define FEE_STRAT_CONSERVATIVE   "CONSERVATIVE"
#define FEE_STRAT_ECONOMICAL     "ECONOMICAL"

enum JSON_StateEnum
{
   JSON_null,
   JSON_true,
   JSON_false
};

////////////////////////////////////////////////////////////////////////////////
class JSON_Exception : public runtime_error
{
public:
   JSON_Exception(const string& str) : runtime_error(str)
   {}
};

////////////////////////////////////////////////////////////////////////////////
struct JSON_value
{
   virtual ~JSON_value(void) = 0;
   virtual void serialize(ostream&) const = 0;
};

struct JSON_array;

////////////////////////////////////////////////////////////////////////////////
struct JSON_string : JSON_value
{
   string val_;

   JSON_string(void)
   {}

   JSON_string(const string& val) : val_(val)
   {}

   void serialize(ostream& s) const
   {
      s << "\"" << val_ << "\"";
   }

   void unserialize(istream& s);

   bool operator<(const JSON_string& rhs) const
   {
      return val_ < rhs.val_;
   }
};

////////////////////////////////////////////////////////////////////////////////
struct JSON_number : JSON_value
{
   double val_;

   JSON_number(void)
   {}
   
   JSON_number(double val) : val_(val)
   {}

   JSON_number(int val) : val_(double(val))
   {}

   JSON_number(unsigned val) : val_(double(val))
   {}

   void serialize(ostream& s) const
   {
      s << val_;
   }

   void unserialize(istream& s)
   {
      s >> val_;
   }
};

////////////////////////////////////////////////////////////////////////////////
struct JSON_state : JSON_value
{
   JSON_StateEnum state_ = JSON_null;

   void serialize(ostream& s) const
   {
      if (state_ == JSON_null)
         s << "null";
      else if (state_ == JSON_true)
         s << "true";
      else if (state_ == JSON_false)
         s << "false";
      else
         throw JSON_Exception("unexpected state at ser");
   }

   void unserialize(istream& s);
};

////////////////////////////////////////////////////////////////////////////////
struct JSON_object : public JSON_value
{
private:
   static int id_counter_;

public:
   map<JSON_string, shared_ptr<JSON_value>> keyval_pairs_;

public:
   const int id_;

   JSON_object(void) :
      id_(id_counter_++)
   {}

   bool add_pair(const string& key, const string& val)
   {
      auto jsonstr = make_shared<JSON_string>(val);
      auto&& keyval = make_pair(
         move(JSON_string(key)), dynamic_pointer_cast<JSON_value>(jsonstr));

      auto insert_iter = keyval_pairs_.insert(move(keyval));
      return insert_iter.second;
   }

   bool add_pair(const string& key, shared_ptr<JSON_value> val)
   {
      auto&& keyval = make_pair(move(JSON_string(key)), val);

      auto insert_iter = keyval_pairs_.insert(move(keyval));
      return insert_iter.second;
   }

   bool add_pair(const string& key, JSON_array& val)
   {
      auto jsonarr = make_shared<JSON_array>(move(val));
      auto&& keyval = make_pair(
         move(JSON_string(key)), dynamic_pointer_cast<JSON_value>(jsonarr));

      auto insert_iter = keyval_pairs_.insert(move(keyval));
      return insert_iter.second;
   }

   bool add_pair(const string& key, float val)
   {
      auto jsonarr = make_shared<JSON_number>(val);
      auto&& keyval = make_pair(
         move(JSON_string(key)), dynamic_pointer_cast<JSON_value>(jsonarr));

      auto insert_iter = keyval_pairs_.insert(move(keyval));
      return insert_iter.second;
   }

   bool add_pair(const string& key, int val)
   {
      return add_pair(key, float(val));
   }

   void serialize(ostream& s) const;
   void unserialize(istream& s);

   shared_ptr<JSON_value> getValForKey(const string&);
   bool isResponseValid(int);
};

////////////////////////////////////////////////////////////////////////////////
struct JSON_array : public JSON_value
{
   vector<shared_ptr<JSON_value>> values_;

   void add_value(string& val)
   {
      auto jsonstr = make_shared<JSON_string>(val);
      values_.push_back(dynamic_pointer_cast<JSON_value>(jsonstr));
   }

   void add_value(unsigned val)
   {
      auto jsonnum = make_shared<JSON_number>(val);
      values_.push_back(dynamic_pointer_cast<JSON_value>(jsonnum));
   }

   void add_value(shared_ptr<JSON_value> valptr)
   {
      values_.push_back(valptr);
   }

   void serialize(ostream& s) const
   {
      s << "[";

      if (values_.size() > 0)
      {
         auto iter = values_.begin();

         while (1)
         {
            (*iter)->serialize(s);

            ++iter;
            if (iter == values_.end())
               break;

            s << ", ";
         }
      }

      s << "]";
   }

   void unserialize(istream&);
};

string JSON_encode(JSON_object& json_obj);
JSON_object JSON_decode(const string& json_str);

#endif
