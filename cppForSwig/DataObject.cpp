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
void ErrorType::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(ERRTYPE_CODE);
   bw.put_var_int(err_.size());
   bw.put_BinaryData((uint8_t*)err_.c_str(), err_.size());
}

///////////////////////////////////////////////////////////////////////////////
ErrorType ErrorType::deserialize(BinaryRefReader& brr)
{
   auto type_code = brr.get_uint8_t();
   if (type_code != ERRTYPE_CODE)
      BtcUtils::throw_type_error(ERRTYPE_CODE, type_code);

   auto size = brr.get_var_int();
   if (size > brr.getSizeRemaining())
      throw runtime_error("invalid data len");

   return ErrorType(string((char*)brr.getCurrPtr(), size));
}

///////////////////////////////////////////////////////////////////////////////
void LedgerEntryVector::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(LEDGERENTRYVECTOR_CODE);
   bw.put_var_int(leVec_.size());

   for (auto& le : leVec_)
   {
      auto idSize = le.ID_.size();
      size_t totalsize = idSize + 53;
      bw.put_var_int(totalsize);

      bw.put_var_int(idSize);
      bw.put_BinaryData((uint8_t*)le.ID_.c_str(), idSize);
      
      bw.put_uint64_t(le.value_);
      bw.put_uint32_t(le.blockNum_);
      bw.put_BinaryData(le.txHash_);
      bw.put_uint32_t(le.index_);
      bw.put_uint32_t(le.txTime_);

      BitPacker<uint8_t> bp;
      bp.putBit(le.isCoinbase_);
      bp.putBit(le.isSentToSelf_);
      bp.putBit(le.isChangeBack_);
      bp.putBit(le.optInRBF_);
      bp.putBit(le.isChainedZC_);
      bp.putBit(le.isWitness_);

      bw.put_BitPacker(bp);

      bw.put_var_int(le.scrAddrVec_.size());
      for (auto& scrAddr : le.scrAddrVec_)
      {
         bw.put_var_int(scrAddr.getSize());
         bw.put_BinaryData(scrAddr);
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
LedgerEntryVector LedgerEntryVector::deserialize(BinaryRefReader& brr)
{
   LedgerEntryVector lev;

   auto type_code = brr.get_uint8_t();
   if (type_code != LEDGERENTRYVECTOR_CODE)
      BtcUtils::throw_type_error(LEDGERENTRYVECTOR_CODE, type_code);


   auto count = brr.get_var_int();

   for (unsigned i = 0; i < count; i++)
   {
      auto leSize = brr.get_var_int();
      if (leSize > brr.getSizeRemaining())
         throw runtime_error("deser size mismatch");

      auto idSize = brr.get_var_int();
      if (idSize + 53 != leSize)
         throw runtime_error("deser size mismatch");

      string leid((char*)brr.getCurrPtr(), idSize);
      brr.advance(idSize);

      auto value = (int64_t*)brr.getCurrPtr();
      brr.advance(8);

      auto blockNum = brr.get_uint32_t();
      auto txHash = brr.get_BinaryDataRef(32);
      auto txindex = brr.get_uint32_t();
      auto txTime = brr.get_uint32_t();

      BitUnpacker<uint8_t> bit(brr.get_uint8_t());
      auto coinbase = bit.getBit();
      auto sts = bit.getBit();
      auto change = bit.getBit();
      auto rbf = bit.getBit();
      auto chained = bit.getBit();
      auto witness = bit.getBit();

      set<BinaryData> scrAddrSet;
      auto count = brr.get_var_int();
      for (unsigned y = 0; y < count; y++)
      {
         auto len = brr.get_var_int();
         auto&& scrAddr = brr.get_BinaryData(len);
         scrAddrSet.insert(move(scrAddr));
      }

      LedgerEntryData led(leid, *value,
         blockNum, txHash, txindex, txTime,
         coinbase, sts, change, rbf, chained, witness, scrAddrSet);

      lev.push_back(move(led));
   }

   return lev;
}

///////////////////////////////////////////////////////////////////////////////
void BinaryDataObject::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(BINARYDATAOBJECT_CODE);
   bw.put_var_int(bd_.getSize());
   bw.put_BinaryData(bd_);
}

///////////////////////////////////////////////////////////////////////////////
BinaryDataObject BinaryDataObject::deserialize(BinaryRefReader& brr)
{
   auto type_code = brr.get_uint8_t();
   if (type_code != BINARYDATAOBJECT_CODE)
      BtcUtils::throw_type_error(BINARYDATAOBJECT_CODE, type_code);

   auto size = brr.get_var_int();
   if (size > brr.getSizeRemaining())
      throw runtime_error("invalid bdo size");

   return BinaryDataObject(brr.get_BinaryDataRef(size));
}

///////////////////////////////////////////////////////////////////////////////
void BinaryDataVector::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(BINARYDATAVECTOR_CODE);
   size_t size = 0;
   for (auto& bdo : bdVec_)
      size += bdo.getSize();

   bw.put_var_int(size);
   bw.put_var_int(bdVec_.size());

   for (auto& bdo : bdVec_)
   {
      bw.put_var_int(bdo.getSize());
      bw.put_BinaryData(bdo);
   }
}

///////////////////////////////////////////////////////////////////////////////
BinaryDataVector BinaryDataVector::deserialize(BinaryRefReader& brr)
{
   auto type_code = brr.get_uint8_t();
   if (type_code != BINARYDATAVECTOR_CODE)
      BtcUtils::throw_type_error(BINARYDATAVECTOR_CODE, type_code);

   auto size = brr.get_var_int();
   if (size > brr.getSizeRemaining())
      throw runtime_error("invalid bdvec size");

   BinaryDataVector bdvec;

   auto count = brr.get_var_int();
   for (unsigned i = 0; i < count; i++)
   {
      auto bdsize = brr.get_var_int();
      if (bdsize > brr.getSizeRemaining())
         throw runtime_error("invalid bd size");

      auto&& bdo = brr.get_BinaryData(bdsize);

      bdvec.push_back(move(bdo));
   }

   return bdvec;
}

///////////////////////////////////////////////////////////////////////////////
void ProgressData::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(PROGRESSDATA_CODE);

   bw.put_uint8_t((uint8_t)phase_);
   bw.put_double(progress_);
   bw.put_uint32_t(time_);
   bw.put_uint32_t(numericProgress_);
   
   //wlt IDs
   bw.put_var_int(wltIDs_.size());

   for (auto& id : wltIDs_)
   {
      bw.put_var_int(id.size());

      BinaryDataRef idBdr((uint8_t*)id.c_str(), id.size());
      bw.put_BinaryDataRef(idBdr);
   }
}

///////////////////////////////////////////////////////////////////////////////
ProgressData ProgressData::deserialize(BinaryRefReader& brr)
{
   auto type_code = brr.get_uint8_t();
   if (type_code != PROGRESSDATA_CODE)
      BtcUtils::throw_type_error(PROGRESSDATA_CODE, type_code);

   ProgressData pd;
   pd.phase_ = (BDMPhase)brr.get_uint8_t();
   pd.progress_ = brr.get_double();
   pd.time_ = brr.get_uint32_t();
   pd.numericProgress_ = brr.get_uint32_t();

   //wlt IDs
   auto idCount = brr.get_var_int();
   for (unsigned i = 0; i < idCount; i++)
   {
      auto idLen = brr.get_var_int();
      auto idBdr = brr.get_BinaryDataRef(idLen);

      pd.wltIDs_.push_back(move(string((char*)idBdr.getPtr(), idLen)));
   }

   return pd;
}

///////////////////////////////////////////////////////////////////////////////
void IntType::serialize(BinaryWriter& bw) const
{
   bw.put_uint8_t(INTTYPE_CODE);
   bw.put_var_int(val_);
}

///////////////////////////////////////////////////////////////////////////////
IntType IntType::deserialize(BinaryRefReader& brr)
{
   auto type_code = brr.get_uint8_t();
   if (type_code != INTTYPE_CODE)
      BtcUtils::throw_type_error(INTTYPE_CODE, type_code);

   return IntType(brr.get_var_int());
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
      setRawData();
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

   BinaryWriter bw;
   for (auto& arg : argData_)
      arg->serialize(bw);

   auto& bdser = bw.getData();
   argStr_ = move(bdser.toHexStr());

   return argStr_;
}

///////////////////////////////////////////////////////////////////////////////
void Arguments::setRawData()
{
   rawBinary_ = READHEX(argStr_);
   rawRefReader_.setNewData(rawBinary_);
}

///////////////////////////////////////////////////////////////////////////////
//
// Command
//
///////////////////////////////////////////////////////////////////////////////
void Command::deserialize()
{
   //sanity check
   if (command_.size() < 8)
      throw runtime_error("command is too short");

   //split checksum from packet
   auto&& checksum = command_.substr(0, 8);
   auto&& packet = command_.substr(8);

   //verify checksum
   auto&& hash = BtcUtils::getHash256(packet);
   if (hash.getSliceRef(0, 4).toHexStr() != checksum)
   {
      LOGERR << "command checksum failure";
      throw runtime_error("command checksum failure");
   }

   //find dot delimiter
   string ids;
   size_t pos = packet.find('.');
   if (pos == string::npos)
      ids = packet;
   else
   {
      ids = packet.substr(0, pos);
      args_ = move(Arguments(packet.substr(pos + 1)));
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

   //hash the packet
   auto&& packet = ss.str();
   auto&& hash = BtcUtils::getHash256(packet);
   
   //prepend first 4 bytes of hash as checksum
   command_ = hash.getSliceRef(0, 4).toHexStr();
   command_.append(packet);
}

///////////////////////////////////////////////////////////////////////////////
//
// Callback
//
///////////////////////////////////////////////////////////////////////////////
void Callback::callback(Arguments&& cmd, OrderType type)
{
   OrderStruct order(move(cmd), type);
   cbStack_.push_back(move(order));
}
