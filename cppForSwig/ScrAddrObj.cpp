#include "ScrAddrObj.h"

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// ScrAddrObj Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
ScrAddrObj::ScrAddrObj(HashString    addr, 
                       uint32_t      firstBlockNum,
                       uint32_t      firstTimestamp,
                       uint32_t      lastBlockNum,
                       uint32_t      lastTimestamp) :
      scrAddr_(addr), 
      firstBlockNum_(firstBlockNum), 
      firstTimestamp_(firstTimestamp),
      lastBlockNum_(lastBlockNum), 
      lastTimestamp_(lastTimestamp)
{ 
   relevantTxIOPtrs_.clear();
   relevantTxIOPtrsZC_.clear();
} 



////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getSpendableBalance(
   InterfaceToLDB *db,
   uint32_t currBlk, bool ignoreAllZC
) const
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
     if(relevantTxIOPtrs_[i]->isSpendable(db, currBlk, ignoreAllZC))
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
     if(relevantTxIOPtrsZC_[i]->isSpendable(db, currBlk, ignoreAllZC))
         balance += relevantTxIOPtrsZC_[i]->getValue();
   }
   return balance;
}


////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getUnconfirmedBalance(
   InterfaceToLDB *db,
   uint32_t currBlk, bool inclAllZC
) const
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      if(relevantTxIOPtrs_[i]->isMineButUnconfirmed(db, currBlk, inclAllZC))
         balance += relevantTxIOPtrs_[i]->getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      if(relevantTxIOPtrsZC_[i]->isMineButUnconfirmed(db, currBlk, inclAllZC))
         balance += relevantTxIOPtrsZC_[i]->getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t ScrAddrObj::getFullBalance(InterfaceToLDB *db) const
{
   uint64_t balance = 0;
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isUnspent(db))
         balance += txio.getValue();
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isUnspent(db))
         balance += txio.getValue();
   }
   return balance;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getSpendableTxOutList(
   InterfaceToLDB *db,
   uint32_t blkNum,
   bool ignoreAllZC
)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isSpendable(db, blkNum, ignoreAllZC))
      {
         TxOut txout = txio.getTxOutCopy(db);
         utxoList.push_back( UnspentTxOut(db, txout, blkNum) );
      }
   }

   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isSpendable(db, blkNum, ignoreAllZC))
      {
         TxOut txout = txio.getTxOutCopy(db);
         utxoList.push_back( UnspentTxOut(db, txout, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
vector<UnspentTxOut> ScrAddrObj::getFullTxOutList(InterfaceToLDB *db, uint32_t blkNum)
{
   vector<UnspentTxOut> utxoList(0);
   for(uint32_t i=0; i<relevantTxIOPtrs_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrs_[i];
      if(txio.isUnspent(db))
      {
         TxOut txout = txio.getTxOutCopy(db);
         utxoList.push_back( UnspentTxOut(db, txout, blkNum) );
      }
   }
   for(uint32_t i=0; i<relevantTxIOPtrsZC_.size(); i++)
   {
      TxIOPair & txio = *relevantTxIOPtrsZC_[i];
      if(txio.isUnspent(db))
      {
         TxOut txout = txio.getTxOutCopy(db);
         utxoList.push_back( UnspentTxOut(db, txout, blkNum) );
      }
   }
   return utxoList;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t ScrAddrObj::removeInvalidEntries(void)   
{
   vector<LedgerEntry> newLedger(0);
   uint32_t leRemoved = 0;
   for(uint32_t i=0; i<ledger_.size(); i++)
   {
      if(!ledger_[i].isValid())
         leRemoved++;
      else
         newLedger.push_back(ledger_[i]);
   }
   ledger_.clear();
   ledger_ = newLedger;
   return leRemoved;
}
   
////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::sortLedger(void)
{
   sort(ledger_.begin(), ledger_.end());
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addLedgerEntry(LedgerEntry const & le, bool isZeroConf)
{ 
   if(isZeroConf)
      ledgerZC_.push_back(le);
   else
      ledger_.push_back(le);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::addTxIO(TxIOPair * txio, bool isZeroConf)
{ 
   if(isZeroConf)
      relevantTxIOPtrsZC_.push_back(txio);
   else
      relevantTxIOPtrs_.push_back(txio);
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::pprintLedger() const
{ 
   cout << "Address Ledger: " << getScrAddr().toHexStr() << endl;
   for(uint32_t i=0; i<ledger_.size(); i++)
      ledger_[i].pprintOneLine();
   for(uint32_t i=0; i<ledgerZC_.size(); i++)
      ledgerZC_[i].pprintOneLine();
}

////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearBlkData(void)
{
   relevantTxIOPtrs_.clear();
   relevantTxIOPtrsZC_.clear();
   ledger_.clear();
   ledgerZC_.clear();
}


////////////////////////////////////////////////////////////////////////////////
void ScrAddrObj::clearZeroConfPool(void)
{
   ledgerZC_.clear();
   relevantTxIOPtrsZC_.clear();
}

