#include "ScrAddrObj.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(InterfaceToLDB *db, HashString    addr, 
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp,
                       uint32_t      lastBlockNum,
                       uint32_t      lastTimestamp) :
      db_(db),
      scrAddr_(addr), 
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp),
      lastBlockNum_(lastBlockNum), 
      lastTimestamp_(lastTimestamp)
{ 
   relevantTxIO_.clear();
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getSpendableBalance(
   uint32_t currBlk, bool ignoreAllZC
) const
{
   uint64_t balance = 0;
   for(auto txio : relevantTxIO_)
   {
     if(txio.second.isSpendable(db_, currBlk, ignoreAllZC))
         balance += txio.second.getValue();
   }
   return balance;
}


////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getUnconfirmedBalance(
   uint32_t currBlk, bool inclAllZC
) const
{
   uint64_t balance = 0;
   for (auto txio : relevantTxIO_)
   {
      if(txio.second.isMineButUnconfirmed(db_, currBlk, inclAllZC))
         balance += txio.second.getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getFullBalance() const
{
   uint64_t balance = 0;
   for(auto txio : relevantTxIO_)
   {
      if(txio.second.isUnspent(db_))
         balance += txio.second.getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getSpendableTxOutList(
   uint32_t blkNum,
   bool ignoreAllZC
) const
{
   vector<UnspentTxOut> utxoList(0);
   for (auto txio : relevantTxIO_)
   {
      if(txio.second.isSpendable(db_, blkNum, ignoreAllZC))
      {
         TxOut txout = txio.second.getTxOutCopy(db_);
         utxoList.push_back( UnspentTxOut(db_, txout, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getFullTxOutList(uint32_t blkNum) const
{
   vector<UnspentTxOut> utxoList(0);
   for (auto txio : relevantTxIO_)
   {
      if(txio.second.isUnspent(db_))
      {
         TxOut txout = txio.second.getTxOutCopy(db_);
         utxoList.push_back( UnspentTxOut(db_, txout, blkNum) );
      }
   }
   return utxoList;
}
   
////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addTxIO(TxIOPair& txio, bool isZeroConf)
{ 
   relevantTxIO_[txio.getDBKeyOfOutput()] = txio;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::pprintLedger() const 
{ 
   cout << "Address Ledger: " << getScrAddr().toHexStr() << endl;
   for(const auto ledger : ledger_)
      ledger.second.pprintOneLine();
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearBlkData(void)
{
   relevantTxIO_.clear();
   ledger_.clear();
   totalTxioCount_ = 0;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateTxIOMap(map<BinaryData, TxIOPair>& txio_map)
{
   for (auto txio : txio_map)
   {
      relevantTxIO_[txio.first] = txio.second;
      //if (txio.second.hasTxIn())
         //relevantTxIO_.erase(txio)
   }
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::scanZC(const map<HashString, TxIOPair>& zcTxIOMap)
{
   for (auto txioPair : zcTxIOMap)
      relevantTxIO_[txioPair.first] = txioPair.second;

   updateLedgers(nullptr, zcTxIOMap);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::purgeZC(const vector<BinaryData>& invalidatedTxOutKeys)
{
   for (auto zc : invalidatedTxOutKeys)
   {
      auto txioIter = relevantTxIO_.find(zc);

      if (ITER_IN_MAP(txioIter, relevantTxIO_))
      {
         TxIOPair& txio = txioIter->second;

         if (txio.hasTxInZC())
         {
            //ZC consumes UTxO, reset the TxIn to mark the TxOut as unspent
            BinaryData zckey = getLedgerKey(txio.getDBKeyOfInput(), false);
            ledger_.erase(zckey);

            txio.setTxIn(BinaryData(0));
            txio.setTxHashOfInput(BinaryData(0));
         }

         if (txio.hasTxOutZC())
         {
            //purged ZC chain, remove the TxIO
            relevantTxIO_.erase(txioIter);
            ledger_.erase(zc);
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateAfterReorg(uint32_t lastValidBlockHeight)
{
   auto txioIter = relevantTxIO_.begin();

   uint32_t height;
   while (txioIter != relevantTxIO_.end())
   {
      //txio pairs are saved by TxOut DBkey, if the key points to a block 
      //higher than the reorg point, delete the txio
      height = DBUtils::hgtxToHeight(txioIter->first.getSliceCopy(0, 4));

      if (height >= 0xFF000000)
      {
         //ZC chain, already dealt with by the call to purgeZC from 
         //readBlkFileUpdate
         continue;
      }
      else if (height <= lastValidBlockHeight)
      {
         TxIOPair& txio = txioIter->second;
         if (txio.hasTxIn())
         {
            //if the txio is spent, check the block of the txin
            height = DBUtils::hgtxToHeight(
               txio.getDBKeyOfInput().getSliceCopy(0, 4));

            if (height > lastValidBlockHeight && height < 0xFF000000)
            {
               //clear the TxIn by setting it to an empty BinaryData
               txio.setTxIn(BinaryData(0));
               txio.setTxHashOfInput(BinaryData(0));
            }
         }

         ++txioIter;
      }
      else
         relevantTxIO_.erase(txioIter++);
   }
}

////////////////////////////////////////////////////////////////////////////////
BinaryData ScrAddrObj::getLedgerKey(const BinaryData& DBkey, bool isTxOut)
{
   /***converts DBkey to Ledger key.
   DBkeys are:
      hgtX/txid/txoutid
   and for ZC transactions:
      0xFF/ZCid/txout-or-in_id

   for a total of 8 bytes. DBkeys are unique within TxOuts, as well as within
   TxIns. However, since they use the same format, they can collide when mixed.
   There is no collision issues with TxIOPairs, as the class differenciates 
   the 2 type of keys and uses the respective DB wrapper methods to fetch them 
   from DB.

   For ZC, TxOuts are differentiated from TxIns in the last 2 bytes 
   (txout-or-in_id). If the top bit is flagged, the key refers to a txin.
   The same method will be used to differentiate TxIns and TxOuts within ledger
   keys.

   While TxIOPairs keep TxIns associated with their originating TxOuts, ledgers 
   separate them, and saves them by their DBkey, which mixes TxOut and TxIn 
   DBkeys.
   
   This method is used to convert DBkeys to Ledger keys, in order to avoid 
   collisions at ledger level.

   This method has no effect on TxOut DBkeys.
   ***/

   if (!isTxOut && DBkey.getSize()==8)
   {
      BinaryData LedgerKey = DBkey;
      
      uint8_t* keyPtr = LedgerKey.getPtr();
      keyPtr[6] |= 0xF0;

      return LedgerKey;
   }

   return DBkey;
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::updateLedgers(const Blockchain* bc,
                               const map<BinaryData, TxIOPair>& newTxio)
{
   /***
   Nothing too complicated here. A map of new TxIOPair ordered by TxOut DBkey
   are parsed to create the respective scrAddr ledger entries. 
   
   A TxIn is a spend, thus the ledger entry value will be negative. 
   A TxOut marks received funds, and will have a positive value. 

   TxIOPairs carry the coinbase distiction at SSH level.
   There is no concept of change at scrAddr level.

   Height and index are derived from DBkeys.
   
   The TxHash is queried from the db since it isn't carried by the TxIOPair.
   The timestamp is the block timestamp. Blockchain objects do not allow to
   query blocks by height AND dup, and will only block headers for the main
   for any given height, however that is irrelevant here, as only main branch 
   transactions make it into SSH objects.
   ***/

   BinaryData opKey;
   BinaryData inKey;
   BlockHeader*  bhptr;
   uint32_t txtime;

   uint32_t opHeight;
   uint32_t inHeight;
   uint32_t opIdx;
   uint32_t inIdx;

   for (auto txioPair : newTxio)
   {
      const TxIOPair& txio = txioPair.second;
      opKey = txio.getDBKeyOfOutput();

      if (ledger_.find(opKey) == ledger_.end())
      {
         if ((uint16_t)*opKey.getSliceRef(0, 2).getPtr() == 0xFF)
         {
            opHeight = UINT32_MAX;
            opIdx = READ_UINT32_BE(opKey.getSliceRef(2, 4));
         }
         else
         {
            opHeight = DBUtils::hgtxToHeight(opKey.getSliceRef(0, 4));
            opIdx = READ_UINT16_BE(opKey.getSliceRef(6, 2));
         }

         if (bc != nullptr)
         {
            bhptr = &bc->getHeaderByHeight(opHeight);
            txtime = bhptr->getTimestamp();
         }
         else
            txtime = txio.getTxTime();

         LedgerEntry le(scrAddr_,
            txio.getValue(),
            opHeight,
            txio.getTxHashOfOutput(db_),
            opIdx,
            txtime,
            txio.isFromCoinbase());

         ledger_[opKey] = le;
      }

      if (txio.hasTxIn())
      {
         inKey = getLedgerKey(txio.getDBKeyOfInput(), false);
         if (ledger_.find(inKey) == ledger_.end())
         {
            if ((uint16_t)*inKey.getSliceRef(0, 2).getPtr() == 0xFF)
            {
               inHeight = UINT32_MAX;
               inIdx = READ_UINT32_BE(inKey.getSliceRef(2, 4));
            }
            else
            {
               inHeight = DBUtils::hgtxToHeight(inKey.getSliceRef(0, 4));
               inIdx = READ_UINT16_BE(inKey.getSliceRef(6, 2));
            }
            
            if (bc != nullptr)
            {
               bhptr = &bc->getHeaderByHeight(inHeight);
               txtime = bhptr->getTimestamp();
            }
            else
               txtime = txio.getTxTime();

            LedgerEntry le(scrAddr_,
               (int64_t)txio.getValue() * -1,
               inHeight,
               txio.getTxHashOfInput(db_),
               inIdx,
               txtime);
         
            ledger_[inKey] = le;
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
vector<LedgerEntry> ScrAddrObj::getTxLedgerAsVector(void) const
{
   vector<LedgerEntry> vle;

   for (auto lePair : ledger_)
      vle.push_back(lePair.second);

   return vle;
}