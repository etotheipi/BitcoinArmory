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
   if (purge == true)
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
   int64_t value;
   int64_t valIn, valOut;

   uint32_t blockNum;
   uint32_t txTime;
   uint32_t nHits;
   uint16_t txIndex;
   BinaryData txHash;

   bool isCoinbase;
   bool isChangeBack;
   bool isSendToSelf;

   BinaryData dbKey;

   for (const auto& txioVec : TxnTxIOMap)
   {
      //reset ledger variables
      value = valIn = valOut = 0;
      isCoinbase = isChangeBack = isSendToSelf = false;
      nHits = 0;

      //grab iterator
      auto txioIter = txioVec.second.cbegin();

      //get txhash, block, txIndex and txtime
      if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
      {
         txHash = txioIter->getTxHashOfOutput(db);

         if (!txioIter->hasTxOutZC())
         {
            blockNum = DBUtils::hgtxToHeight(txioIter->getDBKeyOfOutput().getSliceRef(0, 4));
            txIndex = READ_UINT16_BE(txioIter->getDBKeyOfOutput().getSliceRef(4, 2));
            txTime = bc->getHeaderByHeight(blockNum).getTimestamp();
         }
         else
         {
            blockNum = UINT32_MAX;
            txIndex = READ_UINT16_BE(txioIter->getDBKeyOfOutput().getSliceRef(6, 2));
            txTime = txioIter->getTxTime();
         }
      }
      else
      {
         txHash = txioIter->getTxHashOfInput(db);

         if (!txioIter->hasTxInZC())
         {
            blockNum = DBUtils::hgtxToHeight(txioIter->getDBKeyOfInput().getSliceRef(0, 4));
            txIndex = READ_UINT16_BE(txioIter->getDBKeyOfInput().getSliceRef(4, 2));
            txTime = bc->getHeaderByHeight(blockNum).getTimestamp();
         }
         else
         {
            blockNum = UINT32_MAX;
            txIndex = READ_UINT16_BE(txioIter->getDBKeyOfInput().getSliceRef(6, 2));
            txTime = txioIter->getTxTime();
         }
      }

      if (blockNum < startBlock || blockNum > endBlock)
         continue;

      while (txioIter != txioVec.second.cend())
      {
         if (txioIter->getDBKeyOfOutput().startsWith(txioVec.first))
         {
            isCoinbase |= txioIter->isFromCoinbase();
            valIn += txioIter->getValue();
            value += txioIter->getValue();
         }

         if (txioIter->getDBKeyOfInput().startsWith(txioVec.first))
         {
            valOut -= txioIter->getValue();
            value -= txioIter->getValue();

            nHits++;
         }

         ++txioIter;
      }

      if (valIn + valOut == 0)
      {
         value = valIn;
         isSendToSelf = true;
      }
      else if (nHits != 0 && (valIn + valOut) < 0)
         isChangeBack = true;

      LedgerEntry le(ID, "",
         value,
         blockNum,
         txHash,
         txIndex,
         txTime,
         isCoinbase,
         isSendToSelf,
         isChangeBack);

      leMap[txioVec.first] = le;
   }
}

