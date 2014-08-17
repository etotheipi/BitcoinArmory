#include "BlockDataViewer.h"

/////////////////////////////////////////////////////////////////////////////
BlockDataViewer::BlockDataViewer(BlockDataManager_LevelDB* bdm) :
   rescanZC_(false), zeroConfCont_(bdm->getIFace())
{
   db_ = bdm->getIFace();
   bc_ = &bdm->blockchain();
   saf_ = bdm->getScrAddrFilter();

   zcEnabled_ = false;
   zcLiteMode_ = false;
   zcFilename_ = "";

   lastScanned_ = 0;
}

/////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::registerWallet(BtcWallet* wltPtr, bool wltIsNew)
{
   SCOPED_TIMER("registerWallet");
   // Check if the wallet is already registered
   if (registeredWallets_.find(wltPtr) != registeredWallets_.end())
      return false;

   // Add it to the list of wallets to watch
   registeredWallets_.insert(wltPtr);
   wltPtr->setRegistered();

   return true;
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::unregisterWallet(BtcWallet* wltPtr)
{
   registeredWallets_.erase(wltPtr);
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::scanWallets(uint32_t startBlock,
   uint32_t endBlock)
{
   LOGINFO << registeredWallets_.size() << " wallets loaded";
   uint32_t i = 0;
   bool reorg = false;

   if (startBlock == UINT32_MAX)
      startBlock = lastScanned_;
   if (endBlock == UINT32_MAX)
      endBlock = getTopBlockHeight() + 1;

   if (lastScanned_ > startBlock)
      reorg = true;

   for (BtcWallet* walletPtr : registeredWallets_)
   {
      LOGINFO << "initializing wallet #" << i;
      i++;

      walletPtr->scanWallet(startBlock, endBlock, reorg);
   }

  zeroConfCont_.resetNewZC();
  lastScanned_ = endBlock;
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::hasWallet(BtcWallet* wltPtr)
{
   return registeredWallets_.find(wltPtr) != registeredWallets_.end();
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintRegisteredWallets(void) const
{
   for (const BtcWallet *wlt : registeredWallets_)
   {
      cout << "Wallet:";
      wlt->pprintAlittle(cout);
   }
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::addNewZeroConfTx(BinaryData const & rawTx,
   uint32_t txtime,
   bool writeToFile)
{
   SCOPED_TIMER("addNewZeroConfTx");

   if (txtime == 0)
      txtime = (uint32_t)time(nullptr);

   zeroConfCont_.addRawTx(rawTx, txtime);
   rescanZC_ = true;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::enableZeroConf(string zcFilename, bool zcLite)
{
   SCOPED_TIMER("enableZeroConf");
   LOGINFO << "Enabling zero-conf tracking " << (zcLite ? "(lite)" : "");
   zcFilename_ = zcFilename;
   zcEnabled_ = true;
   zcLiteMode_ = zcLite;

   readZeroConfFile(zcFilename_); // does nothing if DNE
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::readZeroConfFile(string zcFilename)
{
   SCOPED_TIMER("readZeroConfFile");
   uint64_t filesize = BtcUtils::GetFileSize(zcFilename);
   if (filesize<8 || filesize == FILE_DOES_NOT_EXIST)
      return;

   ifstream zcFile(zcFilename_.c_str(), ios::in | ios::binary);
   BinaryData zcData((size_t)filesize);
   zcFile.read((char*)zcData.getPtr(), filesize);
   zcFile.close();

   // We succeeded opening the file...
   BinaryRefReader brr(zcData);
   while (brr.getSizeRemaining() > 8)
   {
      uint64_t txTime = brr.get_uint64_t();
      uint32_t txSize = BtcUtils::TxCalcLength(brr.getCurrPtr(), brr.getSizeRemaining());
      BinaryData rawtx(txSize);
      brr.get_BinaryData(rawtx.getPtr(), txSize);
      addNewZeroConfTx(rawtx, (uint32_t)txTime, false);
   }
   purgeZeroConfPool();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::disableZeroConf(void)
{
   SCOPED_TIMER("disableZeroConf");
   zcEnabled_ = false;
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::purgeZeroConfPool()
{
   const map<BinaryData, vector<BinaryData> > invalidatedTxIOKeys
      = zeroConfCont_.purge(
      [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });

   for (auto& wltPtr : registeredWallets_)
   {
      wltPtr->purgeZeroConfTxIO(invalidatedTxIOKeys);
   }
}


////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::rewriteZeroConfFile(void)
{
   /*SCOPED_TIMER("rewriteZeroConfFile");
   ofstream zcFile(zcFilename_.c_str(), ios::out | ios::binary);

   ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);
   ;

   for(ts_BinDataMap::const_iterator iter = listSS.begin();
   iter != listSS.end();
   ++iter)
   {
   const ZeroConfData& zcd = zeroConfMap_[iter->first].get();
   zcFile.write( (char*)(&zcd.txtime_), sizeof(uint64_t) );
   zcFile.write( (char*)(zcd.txobj_.getPtr()),  zcd.txobj_.getSize());
   }

   zcFile.close();*/

}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::pprintZeroConfPool(void) const
{
   /*ts_BinDataMap::const_snapshot listSS(zeroConfRawTxMap_);

   for (ts_BinDataMap::const_iterator iter = listSS.begin();
   iter != listSS.end(); ++iter
   )
   {
   const ZeroConfData & zcd = zeroConfMap_[iter->first];
   const Tx & tx = zcd.txobj_;
   cout << tx.getThisHash().getSliceCopy(0,8).toHexStr().c_str() << " ";
   for(uint32_t i=0; i<tx.getNumTxOut(); i++)
   cout << tx.getTxOutCopy(i).getValue() << " ";
   cout << endl;
   }*/
}

////////////////////////////////////////////////////////////////////////////////
bool BlockDataViewer::parseNewZeroConfTx()
{
   return zeroConfCont_.parseNewZC(
      [this](const BinaryData& sa)->bool { return saf_->hasScrAddress(sa); });
}

bool BlockDataViewer::registerScrAddr(const ScrAddrObj& sa, BtcWallet* wltPtr)
{
   return saf_->registerScrAddr(sa, wltPtr);
}

////////////////////////////////////////////////////////////////////////////////
LedgerEntry BlockDataViewer::getTxLedgerByHash(
   const BinaryData& txHash) const
{
   LedgerEntry le;
   for (const auto& wltPtr : registeredWallets_)
   {
      le = wltPtr->getLedgerEntryForTx(txHash);
      if (le.getTxTime() != 0)
         return le;
   }

   return le;
}

/////////////////////////////////////////////////////////////////////////////
TX_AVAILABILITY BlockDataViewer::getTxHashAvail(BinaryDataRef txHash)
{
   if (db_->getTxRef(txHash).isNull())
   {
      if (!zeroConfCont_.hasTxByHash(txHash))
         return TX_DNE;  // No tx at all
      else
         return TX_ZEROCONF;  // Zero-conf tx
   }
   else
      return TX_IN_BLOCKCHAIN; // In the blockchain already
}

/////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getTxByHash(HashString const & txhash)
{
   LMDB::Transaction batch(&db_->dbs_[BLKDATA]);

   TxRef txrefobj = db_->getTxRef(txhash);

   if (!txrefobj.isNull())
      return txrefobj.attached(db_).getTxCopy();
   else
   {
      // It's not in the blockchain, but maybe in the zero-conf tx list
      return zeroConfCont_.getTxByHash(txhash);
   }
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
TxOut BlockDataViewer::getPrevTxOut(TxIn & txin)
{
   if (txin.isCoinbase())
      return TxOut();

   OutPoint op = txin.getOutPoint();
   Tx theTx = getTxByHash(op.getTxHash());
   uint32_t idx = op.getTxOutIndex();
   return theTx.getTxOutCopy(idx);
}

////////////////////////////////////////////////////////////////////////////////
// We're going to need the BDM's help to get the sender for a TxIn since it
// sometimes requires going and finding the TxOut from the distant past
////////////////////////////////////////////////////////////////////////////////
Tx BlockDataViewer::getPrevTx(TxIn & txin)
{
   if (txin.isCoinbase())
      return Tx();

   OutPoint op = txin.getOutPoint();
   return getTxByHash(op.getTxHash());
}

////////////////////////////////////////////////////////////////////////////////
HashString BlockDataViewer::getSenderScrAddr(TxIn & txin)
{
   if (txin.isCoinbase())
      return HashString(0);

   return getPrevTxOut(txin).getScrAddressStr();
}


////////////////////////////////////////////////////////////////////////////////
int64_t BlockDataViewer::getSentValue(TxIn & txin)
{
   if (txin.isCoinbase())
      return -1;

   return getPrevTxOut(txin).getValue();

}

////////////////////////////////////////////////////////////////////////////////
LMDBBlockDatabase* BlockDataViewer::getDB(void) const
{
   return db_;
}

////////////////////////////////////////////////////////////////////////////////
Blockchain& BlockDataViewer::blockchain(void) const
{
   return *bc_;
}

////////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataViewer::getTopBlockHeight(void) const
{
   return bc_->top().getBlockHeight();
}

////////////////////////////////////////////////////////////////////////////////
void BlockDataViewer::reset()
{
   for (auto wltPtr : registeredWallets_)
      wltPtr->reset();

   rescanZC_   = false;
   zcEnabled_  = false;
   zcLiteMode_ = false;
   zcFilename_.clear();
   
   zeroConfCont_.clear();

   lastScanned_ = 0;
}