////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "DataObject.h"
#include "BtcUtils.h"

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const ErrorType& et)
{
   os << et.err_;

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, ErrorType& et)
{
   is >> et.err_;

   return is;
}

///////////////////////////////////////////////////////////////////////////////
const vector<shared_ptr<DataMeta>> DataMeta::iTypeIDs_ = {
   make_shared<DataObject<int>>(),
   make_shared<DataObject<unsigned int>>(),
   make_shared<DataObject<uint64_t>>(),
   make_shared<DataObject<size_t>>(),
   make_shared<DataObject<string>>(),
   make_shared<DataObject<BinaryDataObject>>(),
   make_shared<DataObject<BinaryDataVector>>(),
   make_shared<DataObject<LedgerEntryVector>>(),
   make_shared<DataObject<UtxoVector>>(),
   make_shared<DataObject<ErrorType>>()
};

map<string, uint32_t> DataMeta::strTypeIDs_;

///////////////////////////////////////////////////////////////////////////////
void DataMeta::initTypeMap()
{
   auto iter = iTypeIDs_.begin();

   while (iter != iTypeIDs_.end())
   {
      auto id = iter - iTypeIDs_.begin();
      strTypeIDs_[(*iter)->getTypeName()] = id;

      iter++;
   }
}

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const LedgerEntryVector& lev)
{
   os << "*" << lev.leVec_.size();

   for (auto& le : lev.leVec_)
   {
      os << "+";
      os << le.getID();
      os << "_" << le.getValue();
      os << "_" << le.getBlockNum();
      os << "_" << le.getTxHash().toHexStr();
      os << "_" << le.getIndex();
      os << "_" << le.getTxTime();
      os << "_" << le.isCoinbase();
      os << "_" << le.isSentToSelf();
      os << "_" << le.isChangeBack();
   }

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, LedgerEntryVector& lev)
{
   lev.leVec_.clear();
   if (is.eof())
      throw runtime_error("reached stream eof");

   char c = 0;
   is.get(c);
   if (c != '*')
      throw runtime_error("malformed LedgerEntryVector argument");

   size_t count;
   is >> count;

   string objstr;
   while (getline(is, objstr, '+'))
   {
      if (objstr.size() == 0)
         continue;

      stringstream objss(move(objstr));

      string ID;
      if (!getline(objss, ID, '_'))
         throw runtime_error("malformed LedgerEntryVector argument");

      int64_t value;
      uint32_t blockNum;
      objss >> value;
      char underscore;
      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");
      objss >> blockNum;

      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");

      string data;
      if (!getline(objss, data, '_'))
         throw runtime_error("malformed LedgerEntryVector argument");
      BinaryData txHash(READHEX(data));

      uint32_t index, txTime;
      bool isCoinbase, isSentToSelf, isChangeBack;
      objss >> index;
      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");

      objss >> txTime;
      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");

      objss >> isCoinbase;
      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");

      objss >> isSentToSelf;
      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed LedgerEntryVector argument");

      objss >> isChangeBack;

      LedgerEntryData le(ID, value, blockNum,
         txHash, index, txTime,
         isCoinbase, isSentToSelf, isChangeBack);
      lev.leVec_.push_back(move(le));
   }

   if (count != lev.leVec_.size())
      throw runtime_error("malformed LedgerEntryVector argument");

   return is;
}

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const UtxoVector& utxovec)
{
   os << "*" << utxovec.vec_.size();

   for (auto& utxo : utxovec.vec_)
   {
      os << "+";
      os << utxo.value_;
      os << "_" << utxo.txHeight_;
      os << "_" << utxo.txOutIndex_;
      os << "_" << utxo.txHash_.toHexStr();
      os << "_" << utxo.script_.toHexStr();
   }

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, UtxoVector& utxovec)
{
   //TODO: add size check on serialized objects to avoid memory attack vectors
   utxovec.vec_.clear();
   if (is.eof())
      throw runtime_error("reached stream eof");

   char c = 0;
   is.get(c);
   if (c != '*')
      throw runtime_error("malformed UtxoVector argument");

   size_t count;
   is >> count;

   string objstr;
   while (getline(is, objstr, '+'))
   {
      if (objstr.size() == 0)
         continue;

      stringstream objss(move(objstr));

      uint64_t value;
      uint32_t blockNum;
      uint32_t txOutIndex;
      char underscore;

      objss >> value;

      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed UtxoVector argument");
      objss >> blockNum;

      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed UtxoVector argument");
      objss >> txOutIndex;

      objss.get(underscore);
      if (underscore != '_')
         throw runtime_error("malformed UtxoVector argument");
      string data;
      if (!getline(objss, data, '_'))
         throw runtime_error("malformed UtxoVector argument");
      auto&& txHash = READHEX(data);

      data.clear();
      getline(objss, data);
      auto&& script = READHEX(data);

      UTXO utxo(value, blockNum, txOutIndex,
         txHash, script);
      utxovec.vec_.push_back(move(utxo));
   }

   if (count != utxovec.vec_.size())
      throw runtime_error("malformed UtxoVector argument");

   return is;
}

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const BinaryDataObject& bdo)
{
   os << "_" << bdo.bd_.toHexStr();

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, BinaryDataObject& bdo)
{
   bdo.bd_.clear();
   if (is.eof())
      throw runtime_error("reached stream eof");

   char c = 0;
   is.get(c);
   if (c != '_')
      throw runtime_error("malfored BinaryDataObject argument");

   string data;
   is >> data;
   bdo.bd_ = READHEX(data);

   return is;
}

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const DataMeta& obj)
{
   /***
   int a = 123 : ~1-_123
   string str("abc") : ~4-+3_abc
   BinaryDataObject(BinaryData("abc")) : ~5-+3_616263
   ***/

   auto entry = DataMeta::strTypeIDs_.find(obj.getTypeName());
   if (entry == DataMeta::strTypeIDs_.end())
   {
      stringstream ss;
      ss << "unknown type: " << obj.getTypeName();
      throw runtime_error(ss.str());
   }

   os << "~" << entry->second << "-";
   obj.serializeToStream(os);
   return os;
}

///////////////////////////////////////////////////////////////////////////////
ostream& operator << (ostream& os, const BinaryDataVector& bdvec)
{
   os << "*" << bdvec.bdVec_.size();

   for (auto& bd : bdvec.bdVec_)
      os << "+" << bd.toHexStr();

   return os;
}

///////////////////////////////////////////////////////////////////////////////
istream& operator >> (istream& is, BinaryDataVector& bdvec)
{
   bdvec.bdVec_.clear();
   if (is.eof())
      throw runtime_error("reached stream eof");

   char c = 0;
   is.get(c);
   if (c != '*')
      throw runtime_error("malformed BinaryDataVector argument");

   size_t count;
   is >> count;

   string objstr;
   while (getline(is, objstr, '+'))
   {
      if (objstr.size() == 0)
         continue; //why is getline so bad?

      auto&& bd = READHEX(objstr);
      bdvec.bdVec_.push_back(move(bd));
   }

   if (count != bdvec.bdVec_.size())
      throw runtime_error("malformed BinaryDataVector argument");

   return is;
}

///////////////////////////////////////////////////////////////////////////////
//
// Arguments
//
///////////////////////////////////////////////////////////////////////////////
void Arguments::init()
{
   if (initialized_)
      return;

   if (argStr_.size() != 0)
   {
      breakdownString();
   }
   else if (argData_.size() != 0)
   {
      serialize();
   }
   else
   {
      throw runtime_error("empty Arguments object");
   }

   initialized_ = true;
}

///////////////////////////////////////////////////////////////////////////////
const string& Arguments::serialize()
{
   if (argStr_.size() != 0)
      return argStr_;

   //all sizes are 2 digits long
   //~size-arg
   stringstream ss;
   for (auto arg : argData_)
      ss << *arg;
   argStr_ = ss.str();

   return argStr_;
}

///////////////////////////////////////////////////////////////////////////////
void Arguments::breakdownString()
{
   if (strArgs_.size() != 0)
      return;

   vector<size_t> vpos;

   size_t pos = 0;
   while ((pos = argStr_.find('~', pos)) != string::npos)
   {
      vpos.push_back(pos);
      pos++;
   }

   if (vpos.size() == 0)
      return;

   vpos.push_back(argStr_.size());
   for (int i = 0; i < vpos.size() - 1; i++)
   {
      ssize_t len = vpos[i + 1] - vpos[i];
      if (len < 0)
         throw range_error("invalid arg length");
      strArgs_.push_back(move(argStr_.substr(vpos[i], len)));
   }
}

///////////////////////////////////////////////////////////////////////////////
//
// Command
//
///////////////////////////////////////////////////////////////////////////////
void Command::deserialize()
{
   //find dot delimiter
   string ids;
   size_t pos = command_.find('.');
   if (pos == string::npos)
      ids = command_;
   else
   {
      ids = command_.substr(0, pos);
      args_ = Arguments(command_.substr(pos + 1));
   }

   //tokensize by &
   vector<size_t> posv;
   pos = 0;
   while ((pos = ids.find('&', pos)) != string::npos)
   {
      posv.push_back(pos);
      pos++;
   }

   if (posv.size() == 0)
      throw runtime_error("no IDs found in command string");

   posv.push_back(ids.size());

   for (int i = 0; i < posv.size() - 1; i++)
   {
      ssize_t len = posv[i + 1] - posv[i] - 1;
      if (len < 0)
         throw range_error("invalid id len");
      ids_.push_back(ids.substr(posv[i] + 1, len));
   }

   method_ = ids_.back();
   ids_.pop_back();
}

///////////////////////////////////////////////////////////////////////////////
//
// Callback
//
///////////////////////////////////////////////////////////////////////////////
void Command::serialize()
{
   if (method_.size() == 0)
      throw runtime_error("empty command");

   stringstream ss;

   for (auto id : ids_)
   {
      //id
      ss << "&" << id;
   }

   ss << "&" << method_;
   ss << ".";
   ss << args_.serialize();

   command_ = move(ss.str());
}

///////////////////////////////////////////////////////////////////////////////
void Callback::callback(Arguments&& cmd, OrderType type)
{
   {
      unique_lock<mutex> lock(mu_);
      //compress new block and refresh commands together
      cbOrder order(move(cmd), type);

      if (type != OrderOther)
      {
         deque<cbOrder> oldQueue = move(cbQueue_);
         cbQueue_.clear();
         for (auto& entry : oldQueue)
         {
            if (entry.otype_ != type)
               cbQueue_.push_back(move(entry));
         }
      }

      cbQueue_.push_back(move(order));
      if (cbQueue_.size() > maxQueue_)
         cbQueue_.pop_front();
   }

   emit();
}
