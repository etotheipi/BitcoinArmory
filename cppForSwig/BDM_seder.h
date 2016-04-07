////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BDM_SEDER_H
#define _BDM_SEDER_H

#include <deque>
#include <condition_variable>
#include "BinaryData.h"
#include "DataObject.h"
#include "LedgerEntryData.h"

enum OrderType
{
   OrderNewBlock,
   OrderRefresh,
   OrderOther
};

///////////////////////////////////////////////////////////////////////////////
class LedgerEntryVector
{
private:
   vector<LedgerEntryData> leVec_;

public:
   LedgerEntryVector(void)
   {}

   LedgerEntryVector(const vector<LedgerEntryData>& lev) :
      leVec_(lev)
   {}

   LedgerEntryVector(vector<LedgerEntryData>&& lev) :
      leVec_(move(lev))
   {}

   void push_back(LedgerEntryData&& led) { leVec_.push_back(move(led)); }

   friend ostream& operator << (ostream&, const LedgerEntryVector&);
   friend istream& operator >> (istream&, LedgerEntryVector&);

   const vector<LedgerEntryData>& toVector(void) const;
};

///////////////////////////////////////////////////////////////////////////////
class BinaryDataObject
{
private:
   BinaryData bd_;

public:
   BinaryDataObject(void)
   {}

   BinaryDataObject(const BinaryData& bd) :
      bd_(bd)
   {}

   friend ostream& operator << (ostream&, const BinaryDataObject&);
   friend istream& operator >> (istream&, BinaryDataObject&);

   const BinaryData& get(void) const
   {
      return bd_;
   }
};

///////////////////////////////////////////////////////////////////////////////
class BinaryDataVector
{
private:
   vector<BinaryData> bdVec_;

public:
   BinaryDataVector(void)
   {}

   BinaryDataVector(vector<BinaryData>&& bdvec) :
      bdVec_(move(bdvec))
   {}

   BinaryDataVector(const vector<BinaryData>& bdvec) :
      bdVec_(bdvec)
   {}

   const vector<BinaryData>& get(void) const { return bdVec_; }

   void push_back(BinaryData&& bd)
   { bdVec_.push_back(move(bd)); }

   friend ostream& operator << (ostream&, const BinaryDataVector&);
   friend istream& operator >> (istream&, BinaryDataVector&);
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
   { breakdownString(); }

   Arguments(const string&& argAsString) :
      argStr_(move(argAsString))
   { breakdownString(); }

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
   template<typename T> void push_back(T& obj)
   {
      shared_ptr<DataMeta> data = make_shared<DataObject<T>>(move(obj));
      argData_.push_back(data);
   }

   ///////////////////////////////////////////////////////////////////////////////
   template<typename T> auto get() -> const T
   {
      if (strArgs_.size() == 0)
         throw runtime_error("exhausted entries in Arguments object");

      stringstream ss(strArgs_.front());
      strArgs_.pop_front();

      char c = 0;
      ss.get(c);
      if (c != '~')
         throw runtime_error("bad argument syntax");

      string objType;
      getline(ss, objType, '-');
      if (objType.size() == 0)
         throw runtime_error("arg missing type marker");
      auto objTypeInt = atoi(objType.c_str());
      if (objTypeInt >= DataMeta::iTypeIDs_.size())
         throw runtime_error("unknown type id in arg");

      auto typeIter = DataMeta::iTypeIDs_.cbegin() + objTypeInt;
      if (!(*typeIter)->isType(typeid(T)))
      {
         stringstream ss;
         ss << "Invalid argument type. Expected: " << typeid(T).name()
            << ", got:" << (*typeIter)->getTypeName() ;
         throw runtime_error(ss.str());
      }

      DataObject<T> dataObj;
      ss >> dataObj;

      return dataObj.getObj();
   }
};

class ReturnValue
{
private:
   shared_ptr<DataMeta> dataPtr_;

public:
   ReturnValue(void)
   {}

   template<typename T> ReturnValue(T& obj)
   {
      dataPtr_ = make_shared<DataObject<T>>(move(obj));
   }

   friend ostream& operator << (ostream&, const ReturnValue&);
};

///////////////////////////////////////////////////////////////////////////////
struct Command
{
   //ser/unser bdvid/walletid/method name
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
   struct cbOrder
   {
      Arguments order_;
      OrderType otype_;

      cbOrder(Arguments&& order, OrderType type) :
         order_(move(order)), otype_(type)
      {}
   };

protected:
   deque<cbOrder> cbQueue_;
   mutex mu_;
   condition_variable cv_;

   static const int maxQueue_ = 5;

public:

   virtual ~Callback() {};
   virtual void emit(void) = 0;

   void callback(Arguments&& cmd, OrderType type = OrderOther);
};

#endif