////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _DATAOBJECT_H
#define _DATAOBJECT_H

#include <typeinfo>
#include <typeindex>
#include <vector>
#include <map>
#include <sstream>
#include <string>
#include <initializer_list>
#include <memory>
#include <deque>
#include <mutex>

#include "DbHeader.h"
#include "BDM_seder.h"
#include "ThreadSafeClasses.h"

using namespace std;

enum OrderType
{
   OrderNewBlock,
   OrderRefresh,
   OrderZC,
   OrderOther,
   OrderProgress,
   OrderTerminate
};

///////////////////////////////////////////////////////////////////////////////
class DataMeta
{
private:
   const type_index t_;

public:
   static map<string, uint32_t> strTypeIDs_;
   static vector<shared_ptr<DataMeta>> iTypeIDs_;

public:
   DataMeta(const type_info& type) :
      t_(type)
   {}

   string getTypeName(void) const
   {
      return t_.name();
   }

   bool isType(type_index in) const { return in == t_; }

   static void initTypeMap(void);

   virtual void serializeToStream(ostream&) const = 0;

   friend ostream& operator << (ostream&, const DataMeta&);
};

template <typename T> class DataObject;

///////////////////////////////////////////////////////////////////////////////
template<typename T> istream& operator >> (istream& is, DataObject<T>& obj)
{
   is >> obj.obj_;
   return is;
}

///////////////////////////////////////////////////////////////////////////////
template<typename T> ostream& operator << (ostream& os, const DataObject<T>& obj)
{
   os << obj.obj_;
   return os;
}

///////////////////////////////////////////////////////////////////////////////
template <typename T> class DataObject : public DataMeta
{
   /***
   serialization headers:
   ~: arg type
   *: object count
   +: length of upcoming object
   -: object
   _: object data
   .: arguments delimiter
   &: id
   ***/

private:
   T obj_;

public:
   DataObject() :
      DataMeta(typeid(T))
   {}

   DataObject(const T& theObject) :
      DataMeta(typeid(T)),
      obj_(theObject)
   {}

   DataObject(T&& theObject) :
      DataMeta(typeid(T)),
      obj_(move(theObject))
   {}

   const T getObj(void) const { return obj_; }

   friend ostream& operator << <> (ostream&, const DataObject<T>&);
   friend istream& operator >> <> (istream&, DataObject<T>&);

void serializeToStream(ostream& os) const { os << obj_; }
};

///////////////////////////////////////////////////////////////////////////////
class ErrorType
{
private:
   string err_;

public:
   ErrorType() 
   {}

   ErrorType(const string& err) :
      err_(err)
   {}

   ErrorType(string&& err) :
      err_(move(err))
   {}

   ErrorType(const char* str) :
      err_(str)
   {}

   friend ostream& operator << (ostream&, const ErrorType&);
   friend istream& operator >> (istream&, ErrorType&);

   const string& what(void) const { return err_; }
};
///////////////////////////////////////////////////////////////////////////////
class Arguments
{
private:
   bool initialized_ = false;
   string argStr_;
   vector<shared_ptr<DataMeta>> argData_;
   deque<string> strArgs_;

   void init(void);

public:
   Arguments(void)
   {}

   Arguments(const string& argAsString) :
      argStr_(argAsString)
   {
      breakdownString();
   }

   Arguments(const string&& argAsString) :
      argStr_(move(argAsString))
   {
      breakdownString();
   }

   Arguments(const vector<shared_ptr<DataMeta>>&& argAsData) :
      argData_(move(argAsData))
   {}

   Arguments(const deque<shared_ptr<DataMeta>>& argAsData)
   {
      argData_.insert(argData_.begin(),
         argAsData.begin(), argAsData.end());
   }

   void breakdownString();
   const string& serialize();

   ///////////////////////////////////////////////////////////////////////////////
   void merge(const Arguments& argIn)
   {
      argData_.insert(argData_.end(),
         argIn.argData_.begin(), argIn.argData_.end());
   }

   ///////////////////////////////////////////////////////////////////////////////
   template<typename T> void push_back(const T& obj)
   {
      shared_ptr<DataMeta> data = make_shared<DataObject<T>>(obj);
      argData_.push_back(data);
   }

   ///////////////////////////////////////////////////////////////////////////////
   template<typename T> void push_back(T&& obj)
   {
      shared_ptr<DataMeta> data = make_shared<DataObject<T>>(move(obj));
      argData_.push_back(data);
   }

   ///////////////////////////////////////////////////////////////////////////////
   const vector<shared_ptr<DataMeta>>& getArgVector(void) const
   {
      return argData_;
   }

   ///////////////////////////////////////////////////////////////////////////////
   template<typename T> auto get() -> T
   {
      if (strArgs_.size() == 0)
      {
         LOGERR << "exhausted entries in Arguments object";
         throw range_error("exhausted entries in Arguments object");
      }

      stringstream ss(strArgs_.front());

      char c = 0;
      ss.get(c);
      if (c != '~')
         throw runtime_error("bad argument syntax");

      string objType;
      getline(ss, objType, '-');
      if (objType.size() == 0)
         throw runtime_error("arg missing type marker");
      unsigned int objTypeInt = (unsigned int)atoi(objType.c_str());
      if (objTypeInt >= DataMeta::iTypeIDs_.size())
         throw runtime_error("unknown type id in arg");

      auto typeIter = DataMeta::iTypeIDs_.cbegin() + objTypeInt;
      if (!(*typeIter)->isType(typeid(T)))
      {
         if ((*typeIter)->isType(typeid(ErrorType)))
         {
            DataObject<ErrorType> errObj;
            ss >> errObj;

            throw DbErrorMsg(errObj.getObj().what());
         }

         stringstream ssErr;
         ssErr << "Invalid argument type. Expected: " << typeid(T).name()
            << ", got:" << (*typeIter)->getTypeName() ;
         throw runtime_error(ssErr.str());
      }

      strArgs_.pop_front();

      DataObject<T> dataObj;
      ss >> dataObj;

      return dataObj.getObj();
   }

   bool hasArgs(void) const
   {
      return strArgs_.size() != 0 || argData_.size() != 0;
   }

   void clear(void)
   {
      argStr_.clear();
      argData_.clear();
      strArgs_.clear();
   }
};

///////////////////////////////////////////////////////////////////////////////
struct Command
{
   //ser/deser bdvid/walletid/method name
   string method_;
   vector<string> ids_;
   Arguments args_;

   string command_;

   Command()
   {}

   Command(const string& command) :
      command_(command)
   {}

   void deserialize(void);
   void serialize(void);
};

///////////////////////////////////////////////////////////////////////////////
class Callback
{
protected:
   
   struct OrderStruct
   {
      Arguments order_;
      OrderType otype_;

      OrderStruct(Arguments&& order, OrderType type) :
         order_(move(order)), otype_(type)
      {}

      OrderStruct(void) 
      {}
   };

   TimedStack<OrderStruct> cbStack_;

public:

   virtual ~Callback() 
   {
      shutdown();
   };

   void callback(Arguments&& cmd, OrderType type = OrderOther);
   bool isValid(void) const { return cbStack_.isValid(); }

   void shutdown(void)
   {
      cbStack_.terminate();
   }
};

#endif
