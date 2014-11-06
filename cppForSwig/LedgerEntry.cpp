#include "LedgerEntry.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// LedgerEntry
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

LedgerEntry LedgerEntry::EmptyLedger_;
map<BinaryData, LedgerEntry> LedgerEntry::EmptyLedgerMap_;
BinaryData LedgerEntry::EmptyID_ = BinaryData(0);
BinaryData LedgerEntry::ZCheader_ = WRITE_UINT16_BE(0xFFFF);

////////////////////////////////////////////////////////////////////////////////
BinaryData const & LedgerEntry::getScrAddr(void) const
{ 
   if (ID_.getSize() == 21) return ID_;
   return EmptyID_;
}

////////////////////////////////////////////////////////////////////////////////
string LedgerEntry::getWalletID(void) const
{
   if (ID_.getSize() != 21) return ID_.toBinStr();
   return string();
}

////////////////////////////////////////////////////////////////////////////////
void LedgerEntry::setScrAddr(BinaryData const & bd)
{ 
   if(bd.getSize() == 21) 
      ID_ = bd; 
}

////////////////////////////////////////////////////////////////////////////////
void LedgerEntry::setWalletID(BinaryData const & bd)
{
   if (bd.getSize() != 21)
      ID_ = bd;
}

////////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator<(LedgerEntry const & le2) const
{
   // TODO: I wanted to update this with txTime_, but I didn't want to c
   //       complicate the mess of changes going in, yet.  Do this later
   //       once everything is stable again.
   //if(       blockNum_ != le2.blockNum_)
      //return blockNum_  < le2.blockNum_;
   //else if(  index_    != le2.index_)
      //return index_     < le2.index_;
   //else if(  txTime_   != le2.txTime_)
      //return txTime_    < le2.txTime_;
   //else
      //return false;
   
   if( blockNum_ != le2.blockNum_)
      return blockNum_ < le2.blockNum_;
   else if( index_ != le2.index_)
      return index_ < le2.index_;
   else
      return false;
   
}

//////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator==(LedgerEntry const & le2) const
{
   //TODO
   //return (blockNum_ == le2.blockNum_ && 
           //index_    == le2.index_ && 
           //txTime_   == le2.txTime_);
   return (blockNum_ == le2.blockNum_ && index_ == le2.index_);
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprint(void)
{
   cout << "LedgerEntry: " << endl;
   cout << "   ScrAddr : " << getScrAddr().toHexStr() << endl;
   cout << "   Value   : " << getValue()/1e8 << endl;
   cout << "   BlkNum  : " << getBlockNum() << endl;
   cout << "   TxHash  : " << getTxHash().toHexStr() << endl;
   cout << "   TxIndex : " << getIndex() << endl;
   cout << "   Coinbase: " << (isCoinbase() ? 1 : 0) << endl;
   cout << "   sentSelf: " << (isSentToSelf() ? 1 : 0) << endl;
   cout << "   isChange: " << (isChangeBack() ? 1 : 0) << endl;
   cout << endl;
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::pprintOneLine(void) const
{
   printf("   Addr:%s Tx:%s:%02d   BTC:%0.3f   Blk:%06d\n", 
                           "   ",
                           getTxHash().getSliceCopy(0,8).toHexStr().c_str(),
                           getIndex(),
                           getValue()/1e8,
                           getBlockNum());
}

//////////////////////////////////////////////////////////////////////////////
bool LedgerEntry::operator>(LedgerEntry const & le2) const
{
   if (blockNum_ != le2.blockNum_)
      return blockNum_ > le2.blockNum_;
   else if (index_ != le2.index_)
      return index_ > le2.index_;
   else
      return false;

}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::purgeLedgerMapFromHeight(
   map<BinaryData, LedgerEntry>& leMap, 
   uint32_t purgeFrom)
{
   //Remove all entries starting this height, included.
   

   BinaryData cutOffHeight(6);
   auto heightPtr = cutOffHeight.getPtr();

   uint8_t* purgeFromPtr = reinterpret_cast<uint8_t*>(&purgeFrom);
   memset(heightPtr, 0, 6);
   heightPtr[0] = purgeFromPtr[2];
   heightPtr[1] = purgeFromPtr[1];
   heightPtr[2] = purgeFromPtr[0];

   auto cutOffIterPair = leMap.equal_range(cutOffHeight);
   leMap.erase(cutOffIterPair.first, leMap.end());
}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::purgeLedgerVectorFromHeight(
  vector<LedgerEntry>& leVec,
  uint32_t purgeFrom)
{
   //Remove all entries starting this height, included.
   uint32_t i = 0;

   for (const auto& le : leVec)
   {
      if (le.getBlockNum() >= purgeFrom)
         break;

      i++;
   }
   
   leVec.erase(leVec.begin() +i, leVec.end());

}

//////////////////////////////////////////////////////////////////////////////
void LedgerEntry::computeLedgerMap(map<BinaryData, LedgerEntry> &leMap,
   const map<BinaryData, TxIOPair>& txioMap,
   uint32_t startBlock, uint32_t endBlock,
   const BinaryData& ID,
   LMDBBlockDatabase* db,
   Blockchain* bc,
   bool purge)
{
   if (purge)
      LedgerEntry::purgeLedgerMapFromHeight(leMap, startBlock);

   //arrange txios by transaction
   map<BinaryData, vector<TxIOPair> > TxnTxIOMap;

   for (const auto& txio : txioMap)
   {
      auto txOutDBKey = txio.second.getDBKeyOfOutput().getSliceCopy(0, 6);

      auto& txioVec = TxnTxIOMap[txOutDBKey];
      txioVec.push_back(txio.second);

      if (txio.second.hasTxIn())
      {
         auto txInDBKey = txio.second.getDBKeyOfInput().getSliceCopy(0, 6);

         auto& txioVec = TxnTxIOMap[txInDBKey];
         txioVec.push_back(txio.second);
      }
   }

   //convert TxIO to ledgers

   for (const auto& txioVec : TxnTxIOMap)
   {
      //reset ledger variables
      BinaryData txHash;

      uint32_t blockNum;
      uint32_t txTime;
      uint16_t txIndex;
      
      //grab iterator
      auto txioIter = txioVec.second.cbegin();

      //get txhash, block, txIndex and txtime
      if (!txioVec.first.startsWith(ZCheader_))
      {
         blockNum = DBUtils::hgtxToHeight(txioVec.first.getSliceRef(0, 4));
         txIndex = READ_UINT16_BE(txioVec.first.getSliceRef(4, 2));
         txTime = bc->getHeaderByHeight(blockNum).getTimestamp();

         txHash = db->getTxHashForLdbKey(txioVec.first);
      }
      else
      {
         blockNum = UINT32_MAX;
         txIndex = READ_UINT16_BE(txioVec.first.getSliceRef(6, 2));
         txTime = txioIter->getTxTime();

         if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
            txHash = txioIter->getTxHashOfOutput(db);
         else if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
            txHash = txioIter->getTxHashOfInput(db);
      }

      if (blockNum < startBlock || blockNum > endBlock)
         continue;

      bool isCoinbase=false;
      int64_t value=0;
      int64_t valIn=0, valOut=0;
      uint32_t nTxInAreOurs = 0, nTxOutAreOurs = 0;
     
      while (txioIter != txioVec.second.cend())
      {
         if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
         {
            isCoinbase |= txioIter->isFromCoinbase();
            valIn += txioIter->getValue();
            value += txioIter->getValue();

            nTxOutAreOurs++;
         }

         if (txioIter->getDBKeyOfInput().startsWith(txioVec.first))
         {
            valOut -= txioIter->getValue();
            value -= txioIter->getValue();

            nTxInAreOurs++;
         }

         ++txioIter;
      }

      bool isSentToSelf = false;
      bool isChangeBack = false;
      
      if (nTxInAreOurs * nTxOutAreOurs > 0)
      {
         //if some of the txins AND some of the txouts are ours, this could be an STS
         //pull the txn and compare the txin and txout counts

         LMDBEnv::Transaction tx(&db->dbEnv_, LMDB::ReadOnly);

         StoredTx stx;
         if (!txioVec.first.startsWith(ZCheader_))
         {
            uint8_t dupId = DBUtils::hgtxToDupID(txioVec.first.getSliceRef(0, 4));
            db->getStoredTx(stx, blockNum, dupId, txIndex, false);
         }
         else
            db->getStoredZcTx(stx, txioVec.first);

         if (stx.numTxOut_ == nTxOutAreOurs)
         {
            value = valIn;
            isSentToSelf = true;
         }
      }
      else if (nTxInAreOurs != 0 && (valIn + valOut) < 0)
         isChangeBack = true;

      LedgerEntry le(ID, "",
         value,
         blockNum,
         txHash,
         txIndex,
         txTime,
         isCoinbase,
         isSentToSelf,
         isChangeBack);

      leMap[txioVec.first] = le;
   }
}

// kate: indent-width 3; replace-tabs on;
