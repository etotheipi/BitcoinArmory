#ifndef _H_LEDGERENTRYDATA_
#define _H_LEDGERENTRYDATA_

#include <set>

///////////////////////////////////////////////////////////////////////////////
class LedgerEntryData
{
   friend class LedgerEntryVector;

private:
   string       ID_;

   int64_t          value_;
   uint32_t         blockNum_;
   BinaryData       txHash_;
   uint32_t         index_;  // either a tx index, txout index or txin index
   uint32_t         txTime_ = 0;
   bool             isCoinbase_ = false;
   bool             isSentToSelf_ = false;
   bool             isChangeBack_ = false;
   bool             optInRBF_ = false;
   bool             isChainedZC_ = false;
   bool             isWitness_ = false;

   vector<BinaryData> scrAddrVec_;

public:

   LedgerEntryData(void) {}
   LedgerEntryData(string ID, int64_t value, uint32_t block,
      const BinaryData& txHash, uint32_t index, uint32_t txtime,
      bool iscoinbase, bool isSTS, bool ischangeback,
      bool isRBF, bool isChained, bool isWitness,
      const set<BinaryData>& bdSet) :
      ID_(ID), value_(value), blockNum_(block), txHash_(txHash),
      index_(index), txTime_(txtime), isCoinbase_(iscoinbase),
      isSentToSelf_(isSTS), isChangeBack_(ischangeback),
      optInRBF_(isRBF), isChainedZC_(isChained), isWitness_(isWitness)
   {
      scrAddrVec_.insert(scrAddrVec_.begin(),
         bdSet.begin(), bdSet.end());
   }

   string              getID(void) const { return ID_; }
   string              getWalletID(void) const { return ID_; }
   int64_t             getValue(void) const     { return value_; }
   uint32_t            getBlockNum(void) const  { return blockNum_; }
   BinaryData const &  getTxHash(void) const    { return txHash_; }
   uint32_t            getIndex(void) const     { return index_; }
   uint32_t            getTxTime(void) const    { return txTime_; }
   bool                isCoinbase(void) const   { return isCoinbase_; }
   bool                isSentToSelf(void) const { return isSentToSelf_; }
   bool                isChangeBack(void) const { return isChangeBack_; }
   bool                isOptInRBF(void) const   { return optInRBF_;  }
   bool                isChainedZC(void) const   { return isChainedZC_; }

   vector<BinaryData> getScrAddrList(void) const { return scrAddrVec_; }
};

#endif