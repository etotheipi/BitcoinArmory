////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "JSON_codec.h"

int JSON_object::id_counter_ = 0;

////////////////////////////////////////////////////////////////////////////////
JSON_value::~JSON_value()
{}

////////////////////////////////////////////////////////////////////////////////
string JSON_encode(JSON_object& json_obj)
{
   //make sure json_obj has jsonrpc, params and id key
   auto rpciter = json_obj.keyval_pairs_.find(string("jsonrpc"));
   if (rpciter == json_obj.keyval_pairs_.end())
      json_obj.add_pair("jsonrpc", "2.0");

   auto paramsiter = json_obj.keyval_pairs_.find(string("params"));
   if (paramsiter == json_obj.keyval_pairs_.end())
   {
      JSON_array arr;
      json_obj.add_pair("params", arr);
   }

   auto iditer = json_obj.keyval_pairs_.find(string("id"));
   if (iditer == json_obj.keyval_pairs_.end())
      json_obj.add_pair("id", json_obj.id_);

   stringstream ss;
   json_obj.serialize(ss);
   return ss.str();
}

////////////////////////////////////////////////////////////////////////////////
void JSON_object::serialize(ostream& s) const
{
   s << "{";

   if (keyval_pairs_.size() > 0)
   {
      auto iter = keyval_pairs_.begin();

      while (1)
      {
         iter->first.serialize(s);
         s << ": ";
         iter->second->serialize(s);

         ++iter;
         if (iter == keyval_pairs_.end())
            break;

         s << ", ";
      }
   }

   s << "}";
}

////////////////////////////////////////////////////////////////////////////////
void JSON_object::unserialize(istream& s)
{
   keyval_pairs_.clear();

   auto val = s.get();
   if (val != '{')
      throw JSON_Exception("invalid object encapsulation");

   auto addPair = [this](JSON_string& key, shared_ptr<JSON_value> val)->void
   {
      auto&& keyval = make_pair(move(key), val);
      keyval_pairs_.insert(move(keyval));
   };

   vector<JSON_string> value_vector;

   while (s.good())
   {
      auto c = s.peek();

      switch (c)
      {
      case ' ':
      case ':':
      case ',':
      {
         s.get();
         continue;
      }

      case '\"':
      {
         auto json_string = make_shared<JSON_string>();
         json_string->unserialize(s);

         if (value_vector.size() == 0)
         {
            value_vector.push_back(json_string->val_);
            break;
         }

         auto key = value_vector.back();
         addPair(key, json_string);
         value_vector.pop_back();

         break;
      }

      case '[':
      {
         if (value_vector.size() == 0)
            throw JSON_Exception("missing object key");

         auto json_array = make_shared<JSON_array>();
         json_array->unserialize(s);

         auto key = value_vector.back();
         addPair(key, json_array);
         value_vector.pop_back();

         break;
      }

      case '{':
      {
         if (value_vector.size() == 0)
            throw JSON_Exception("missing object key");

         auto json_object = make_shared<JSON_object>();
         json_object->unserialize(s);

         auto key = value_vector.back();
         addPair(key, json_object);
         value_vector.pop_back();

         break;
      }

      case '}':
      {
         s.get();
         return;
      }

      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
      case '-':
      {
         if (value_vector.size() == 0)
            throw JSON_Exception("missing object key");

         auto json_number = make_shared<JSON_number>();
         json_number->unserialize(s);

         auto key = value_vector.back();
         addPair(key, json_number);
         value_vector.pop_back();

         break;
      }

      case 't':
      case 'n':
      case 'f':
      {
         if (value_vector.size() == 0)
            throw JSON_Exception("missing object key");

         auto json_state = make_shared<JSON_state>();
         json_state->unserialize(s);

         auto key = value_vector.back();
         addPair(key, json_state);
         value_vector.pop_back();

         break;
      }

      default:
         throw JSON_Exception("unexpected encapsulation");
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void JSON_string::unserialize(istream& s)
{
   val_.clear();

   auto val = s.get();
   if (val != '\"')
      throw JSON_Exception("invalid string encapsulation");

   while (1)
   {
      string str;
      getline(s, str, '\"');
      if (s.rdstate() != ios_base::goodbit)
         throw JSON_Exception("invalid string encapsulation");

      val_.append(str);

      //make sure that delimiting '\"' was no exited
      auto len = str.size();
      if (str.c_str()[len - 1] != '\\')
         break;

      val_.append("\"");
   }
}

////////////////////////////////////////////////////////////////////////////////
void JSON_array::unserialize(istream& s)
{
   values_.clear();

   auto val = s.get();
   if (val != '[')
      throw JSON_Exception("invalid string encapsulation");

   while (s.rdstate() == ios_base::goodbit)
   {
      auto c = s.peek();

      switch (c)
      {
      case ' ':
      case ',':
      {
         s.get();
         continue;
      }

      case '\"':
      {
         auto json_string = make_shared<JSON_string>();
         json_string->unserialize(s);
         values_.push_back(json_string);
         
         break;
      }

      case '[':
      {
         auto json_array = make_shared<JSON_array>();
         json_array->unserialize(s);
         values_.push_back(json_array);

         break;
      }

      case ']':
      {
         s.get();
         return;
      }

      case '{':
      {
         auto json_object = make_shared<JSON_object>();
         json_object->unserialize(s);
         values_.push_back(json_object);

         break;
      }

      case '0':
      case '1':
      case '2':
      case '3':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
      case '-':
      {
         auto json_number = make_shared<JSON_number>();
         json_number->unserialize(s);
         values_.push_back(json_number);

         break;
      }

      default:
         throw JSON_Exception("unexpected encapsulation");
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void JSON_state::unserialize(istream& s)
{
   auto c = s.peek();

   switch (c)
   {
   case 'n':
   {
      string val_null;
      val_null.resize(4);
      s.read(&val_null[0], 5);

      if (val_null != "null")
         throw JSON_Exception("invalid state");

      state_ = JSON_null;
      break;
   }

   case 't':
   {
      string val_true;
      val_true.resize(4);
      s.getline(&val_true[0], 5);

      if (val_true != "true")
         throw JSON_Exception("invalid state");

      state_ = JSON_true;
      break;
   }

   case 'f':
   {
      string val_false;
      val_false.resize(5);
      s.getline(&val_false[0], 6);

      if (val_false != "false")
         throw JSON_Exception("invalid state");

      state_ = JSON_false;
      break;
   }

   default:
      throw JSON_Exception("unexpected state at deser");
   }

   if (s.fail())
      s.clear();
}

////////////////////////////////////////////////////////////////////////////////
JSON_object JSON_decode(const string& json_str)
{
   JSON_object obj;
   stringstream ss(json_str);
   obj.unserialize(ss);
   return obj;
}

////////////////////////////////////////////////////////////////////////////////
shared_ptr<JSON_value> JSON_object::getValForKey(const string& key)
{
   auto&& keyStr = JSON_string(string(key));
   auto pairIter = keyval_pairs_.find(keyStr);
   if (pairIter == keyval_pairs_.end())
      return nullptr;

   return pairIter->second;
}

////////////////////////////////////////////////////////////////////////////////
bool JSON_object::isResponseValid(int id)
{
   //check id
   auto idVal = getValForKey("id");
   auto id_obj = dynamic_pointer_cast<JSON_number>(idVal);

   if (id_obj == nullptr)
      return false;

   if (int(id_obj->val_) != id)
      return false;

   //check "error": null
   auto errorVal = getValForKey("error");
   auto error_obj = dynamic_pointer_cast<JSON_state>(errorVal);

   if (error_obj == nullptr)
      return true;

   if (error_obj->state_ != JSON_null)
      return false;

   return true;
}
