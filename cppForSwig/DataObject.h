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

#define ERRTYPE_CODE             1
#define INTTYPE_CODE             2
#define STRINGTTYPE_CODE         3
#define BINARYDATAOBJECT_CODE    4
#define BINARYDATAVECTOR_CODE    5
#define LEDGERENTRYVECTOR_CODE   6
#define PROGRESSDATA_CODE        7

using namespace std;

enum OrderType
{
   OrderNewBlock,
   OrderRefresh,
   OrderZC,
   OrderOther,
   OrderProgress,
   OrderTerminate,
   OrderNodeStatus,
   OrderBDVError
};

///////////////////////////////////////////////////////////////////////////////
class DataMeta
{
private:
   const type_index t_;

public:   
   DataMeta(const type_info& type) :
      t_(type)
   {}

   string getTypeName(void) const
   {
      return t_.name();
   }

   bool isType(type_index in) const { return in == t_; }
   virtual void serialize(BinaryWriter& bw) const = 0;
};

template <typename T> class DataObject;

///////////////////////////////////////////////////////////////////////////////
template <typename T> class DataObject : public DataMeta
{
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

   void serialize(BinaryWriter& bw) const { obj_.serialize(bw); }
   T deserialize(BinaryDataRef bdr) const { return obj_.deserialize(); }
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

   void serialize(BinaryWriter& bw) const;
   static ErrorType deserialize(BinaryRefReader& brr);

   const string& what(void) const { return err_; }
};

///////////////////////////////////////////////////////////////////////////////
class IntType
{
private:
   uint64_t val_;

public:

   IntType(uint64_t val) : val_(val)
   {}

   IntType(int64_t val)
   {
      memcpy(&val_, &val, 8);
   }

   IntType(uint32_t val) : val_(val)
   {}

   IntType(int32_t val) : val_(val)
   {}

   IntType(bool val) : val_(val)
   {}

#if defined(__APPLE__) && defined(__MACH__)
   IntType(size_t val) : val_(val)
   {}
#endif

   void serialize(BinaryWriter& bw) const;
   static IntType deserialize(BinaryRefReader& brr);

   uint64_t getVal(void) const { return val_; }
   int64_t getSignedVal(void) const { return *(int64_t*)&val_; }
};

///////////////////////////////////////////////////////////////////////////////
class Arguments
{
private:
   bool initialized_ = false;
   string argStr_;
   vector<shared_ptr<DataMeta>> argData_;
   BinaryData rawBinary_;
   BinaryRefReader rawRefReader_;

private:
   void init(void);

   void setFromRVal(Arguments&& arg)
   {
      initialized_ = arg.initialized_;
      argStr_ = move(arg.argStr_);
      argData_ = move(arg.argData_);
      rawBinary_ = move(arg.rawBinary_);
      rawRefReader_.setNewData(rawBinary_);
      rawRefReader_.advance(arg.rawRefReader_.getPosition());
   }

   void setFromRef(const Arguments& arg)
   {
      initialized_ = arg.initialized_;
      argStr_ = arg.argStr_;
      argData_ = arg.argData_;
      rawBinary_ = arg.rawBinary_;
      rawRefReader_.setNewData(rawBinary_);
      rawRefReader_.advance(arg.rawRefReader_.getPosition());
   }

public:
   Arguments(void)
   {}

   Arguments(const string& argAsString) :
      argStr_(argAsString)
   {
      setRawData();
   }

   Arguments(const string&& argAsString) :
      argStr_(move(argAsString))
   {
      setRawData();
   }

   Arguments(const vector<shared_ptr<DataMeta>>&& argAsData) :
      argData_(move(argAsData))
   {}

   Arguments(const deque<shared_ptr<DataMeta>>& argAsData)
   {
      argData_.insert(argData_.begin(),
         argAsData.begin(), argAsData.end());
   }

   Arguments(Arguments&& arg)
   {
      setFromRVal(move(arg));
   }

   Arguments(const Arguments& arg)
   {
      setFromRef(arg);
   }

   Arguments operator=(Arguments&& arg)
   {
      if (this == &arg)
         return *this;

      setFromRVal(move(arg));
      return *this;
   }

   Arguments operator=(const Arguments& arg)
   {
      if (this == &arg)
         return *this;

      setFromRef(arg);
      return *this;
   }

   void setRawData();
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
      //sanity check
      if (rawRefReader_.getSizeRemaining() == 0)
      {
         LOGERR << "exhausted entries in Arguments object";
         throw range_error("exhausted entries in Arguments object");
      }      
      
      //peak at rawRefReader_ first byte
      auto objectTypePtr = rawRefReader_.getCurrPtr();
      
      if (*objectTypePtr == ERRTYPE_CODE)
      {
         auto errObj = ErrorType::deserialize(rawRefReader_);
         //LOGERR << "returned ErrorType: " << errObj.what();
         throw DbErrorMsg(errObj.what());
      }

      return T::deserialize(rawRefReader_);
   }

   bool hasArgs(void) const
   {
      return rawRefReader_.getSizeRemaining() != 0 || argData_.size() != 0;
   }

   void clear(void)
   {
      argStr_.clear();
      argData_.clear();
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
