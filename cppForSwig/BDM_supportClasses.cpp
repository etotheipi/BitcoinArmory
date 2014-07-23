#include "BDM_supportClasses.h"
#include "BlockUtils.h"


///////////////////////////////////////////////////////////////////////////////
//ScrAddrScanData Methods
///////////////////////////////////////////////////////////////////////////////

void ScrAddrScanData::getScrAddrCurrentSyncState()
{
   for (auto scrAddrPair : scrAddrMap_)
      getScrAddrCurrentSyncState(scrAddrPair.first);
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrScanData::getScrAddrCurrentSyncState(
   BinaryData const & scrAddr)
{
   //grab SSH for scrAddr
   StoredScriptHistory ssh;
   bdmPtr_->getIFace()->getStoredScriptHistorySummary(ssh, scrAddr);

   //update scrAddrData lowest scanned block
   setScrAddrLastScanned(scrAddr, ssh.alreadyScannedUpToBlk_);

   if (ssh.totalTxioCount_ == 1)
   {
      //scrAddr only has one UTxO, coming along the SSH summary, let's save it
      auto subsshIter = ssh.subHistMap_.begin();
      auto txioIter = subsshIter->second.txioMap_.begin();
      addUTxO(*txioIter);
   }
}

///////////////////////////////////////////////////////////////////////////////
map<BinaryData, map<BinaryData, TxIOPair> >
ScrAddrScanData::ZCisMineBulkFilter(const Tx & tx,
const BinaryData & ZCkey,
LMDBBlockDatabase* db,
uint32_t txtime,
const ZeroConfContainer *zcd,
bool withSecondOrderMultisig) const
{
   // Since 99.999%+ of all transactions are not ours, let's do the 
   // fastest bulk filter possible, even though it will add 
   // redundant computation to the tx that are ours.  In fact,
   // we will skip the TxIn/TxOut convenience methods and follow the
   // pointers directly to the data we want

   map<BinaryData, map<BinaryData, TxIOPair> > processedTxIO;

   OutPoint op; // reused
   uint8_t const * txStartPtr = tx.getPtr();
   for (uint32_t iin = 0; iin<tx.getNumTxIn(); iin++)
   {
      // We have the txin, now check if it contains one of our TxOuts
      op.unserialize(txStartPtr + tx.getTxInOffset(iin), 36);

      //check ZC txhash first, always cheaper than grabing a stxo from DB,
      //and will always be checked if the tx doesn't hit in DB outpoints.
      if (zcd != nullptr)
      {
         BinaryData opZcKey;
         if (zcd->getKeyForTxHash(op.getTxHash(), opZcKey))
         {
            TxRef outPointRef(opZcKey);
            uint16_t outPointId = op.getTxOutIndex();
            TxIOPair txio(outPointRef, outPointId,
               TxRef(ZCkey), iin);

            Tx chainedZC;
            zcd->getTxByHash(op.getTxHash(), chainedZC);

            const TxOut& chainedTxOut = chainedZC.getTxOutCopy(outPointId);

            txio.setTxHashOfOutput(op.getTxHash());
            txio.setTxHashOfInput(tx.getThisHash());

            txio.setValue(chainedTxOut.getValue());
            txio.setTxTime(txtime);

            auto& key_txioPair = processedTxIO[chainedTxOut.getScrAddressStr()];

            key_txioPair[txio.getDBKeyOfOutput()] = txio;
            continue;
         }
      }


      //fetch the TxOut from DB
      BinaryData opKey = op.getDBkey(db);
      if (opKey.getSize() == 8)
      {
         //found outPoint DBKey, grab the StoredTxOut
         StoredTxOut stxOut;
         if (db->getStoredTxOut(stxOut,
            WRITE_UINT8_LE((uint8_t)DB_PREFIX_TXDATA) +
            opKey))
         {
            if (stxOut.isSpent() == true)
            {
               //spent TxOut, ZC is invalid
               return map<BinaryData, map<BinaryData, TxIOPair> >();
            }

            BinaryData sa = stxOut.getScrAddress();
            if (scrAddrMap_.find(sa) != scrAddrMap_.end())
            {
               TxIOPair txio(TxRef(opKey.getSliceRef(0, 6)), op.getTxOutIndex(),
                  TxRef(ZCkey), iin);

               txio.setTxHashOfOutput(op.getTxHash());
               txio.setTxHashOfInput(tx.getThisHash());
               txio.setValue(stxOut.getValue());
               txio.setTxTime(txtime);

               auto& key_txioPair = processedTxIO[sa];

               key_txioPair[txio.getDBKeyOfOutput()] = txio;
            }
         }
      }
   }

   // Simply convert the TxOut scripts to scrAddrs and check if registered
   for (uint32_t iout = 0; iout<tx.getNumTxOut(); iout++)
   {
      TxOut txout = tx.getTxOutCopy(iout);
      BinaryData scrAddr = txout.getScrAddressStr();
      if (hasScrAddress(scrAddr))
      {
         TxIOPair txio(TxRef(ZCkey), iout);

         txio.setValue(txout.getValue());
         txio.setTxHashOfOutput(tx.getThisHash());
         txio.setTxTime(txtime);
         txio.setUTXO(true);

         auto& key_txioPair = processedTxIO[scrAddr];

         key_txioPair[txio.getDBKeyOfOutput()] = txio;
         continue;
      }

      // It's still possible this is a multisig addr involving one of our 
      // existing scrAddrs, even if we aren't explicitly looking for this multisig
      if (withSecondOrderMultisig && txout.getScriptType() ==
         TXOUT_SCRIPT_MULTISIG)
      {
         BinaryRefReader brrmsig(scrAddr);
         uint8_t PREFIX = brrmsig.get_uint8_t();
         uint8_t M = brrmsig.get_uint8_t();
         uint8_t N = brrmsig.get_uint8_t();
         for (uint8_t a = 0; a<N; a++)
         if (hasScrAddress(HASH160PREFIX + brrmsig.get_BinaryDataRef(20)))
         {
            TxIOPair txio(TxRef(ZCkey), iout);

            txio.setTxHashOfOutput(tx.getThisHash());
            txio.setValue(txout.getValue());
            txio.setTxTime(txtime);
            txio.setUTXO(true);

            auto& key_txioPair = processedTxIO[scrAddr];

            key_txioPair[txio.getDBKeyOfOutput()] = txio;
         }
      }
   }

   // If we got here, it's either non std or not ours
   return processedTxIO;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrScanData::setSSHLastScanned(LMDBBlockDatabase* db, uint32_t height)
{
   LMDBBlockDatabase::Batch batch(db, BLKDATA);
   for (const auto scrAddrPair : scrAddrMap_)
   {
      StoredScriptHistory ssh;
      db->getStoredScriptHistorySummary(ssh, scrAddrPair.first);
      if (!ssh.isInitialized())
         ssh.uniqueKey_ = scrAddrPair.first;

      ssh.alreadyScannedUpToBlk_ = height;

      db->putStoredScriptHistory(ssh);
   }
}

///////////////////////////////////////////////////////////////////////////////
bool ScrAddrScanData::registerScrAddr(const ScrAddrObj& sa, BtcWallet* wltPtr)
{
   /***
   Gets a scrAddr ready for loading. Returns false if the BDM is initialized,
   in which case wltPtr will be called back with the address once it is ready
   ***/
   const BinaryData& scrAddr = sa.getScrAddr();

   //check if the BDM is initialized. There ought to be a better way than
   //checking the top block
   if (bdmPtr_->isRunning() == true)
   {
      //BDM is initialized and maintenance thread is running, check mode
      if (bdmPtr_->config().armoryDbType == ARMORY_DB_SUPER)
      {
         //supernode: nothing to do, signal the wallet that its scrAddr is ready
         wltPtr->preloadScrAddr(scrAddr);

         return false;
      }

      //check DB for the scrAddr's SSH
      LMDBBlockDatabase *db = bdmPtr_->getIFace();

      StoredScriptHistory ssh;
      db->getStoredScriptHistorySummary(ssh, scrAddr);

      uint32_t startBlock = max(sa.getFirstBlockNum(), ssh.alreadyScannedUpToBlk_);
      ScrAddrScanData* sca = new ScrAddrScanData(bdmPtr_);
      sca->setParent(this);
      sca->regScrAddrForScan(scrAddr, startBlock, wltPtr);
      sca->scanScrAddrMapInNewThread();

      return false;
   }
   else
   {
      //BDM isnt initialized yet, the maintenance isnt running, just register
      //the scrAddr and return true.
      scrAddrMap_.insert(make_pair(scrAddr, 0));
      return true;
   }
}

///////////////////////////////////////////////////////////////////////////////
void* scanScrAddrThread(void *in)
{
   ScrAddrScanData* sasd = static_cast<ScrAddrScanData*>(in);

   BlockDataManager_LevelDB* bdmPtr = sasd->getBDM();
   uint32_t startBlock = sasd->scanFrom();
   uint32_t endBlock = bdmPtr->blockchain().top().getBlockHeight() + 1;

   while (startBlock < endBlock)
   {
      //ADD MECHANISM TO DETECT REORGS
      bdmPtr->applyBlockRangeToDB(startBlock, endBlock, sasd);

      startBlock = endBlock;
      endBlock = bdmPtr->blockchain().top().getBlockHeight() + 1;
   }

   sasd->setSSHLastScanned(bdmPtr->getIFace(), endBlock);

   //merge with main ScrAddrScanData object
   sasd->merge();

   //notify the wallets that the scrAddr are ready
   BtcWallet* wltPtr;
   for (auto scrAddrPair : sasd->getScrAddrMap())
   {
      wltPtr = scrAddrPair.second.wltPtr_;

      //make sure the wallet is still loaded
      if (bdmPtr->hasWallet(wltPtr))
         wltPtr->preloadScrAddr(scrAddrPair.first);
   }

   //clean up
   delete sasd;

   return 0;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrScanData::scanScrAddrMapInNewThread()
{
   pthread_t tid;

   pthread_create(&tid, 0, scanScrAddrThread, this);
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrScanData::merge()
{
   /***
   Merge in the scrAddrMap and UTxOs scanned in a side thread with the BDM's
   main ScrAddrScanData
   ***/

   if (parent_ != nullptr)
   {
      //grab merge lock
      while (parent_->mergeLock_.fetch_or(1, memory_order_acquire));

      //merge scrAddrMap_
      parent_->scrAddrMapToMerge_.insert(
         scrAddrMap_.begin(), scrAddrMap_.end());

      //copy only the UTxOs past the height cutoff
      BinaryData cutoffHeight =
         DBUtils::heightAndDupToHgtx(parent_->blockHeightCutOff_, 0);
      cutoffHeight.append(WRITE_UINT32_LE(0));

      auto iter = UTxO_.begin();
      while (iter != UTxO_.end())
      {
         if (*iter > cutoffHeight || *iter == cutoffHeight)
            break;

         ++iter;
      }

      parent_->UTxOToMerge_.insert(iter, UTxO_.end());

      //set mergeFlag
      parent_->mergeFlag_ = true;

      //release merge lock
      parent_->mergeLock_.store(0, memory_order_release);
   }
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrScanData::checkForMerge()
{
   if (mergeFlag_ == true)
   {
      //rescan last 100 blocks to account for new blocks and reorgs
      ScrAddrScanData sca(bdmPtr_);
      sca.scrAddrMap_ = scrAddrMapToMerge_;
      sca.UTxO_ = UTxOToMerge_;

      sca.blockHeightCutOff_ = blockHeightCutOff_;
      uint32_t topBlock = bdmPtr_->blockchain().top().getBlockHeight();
      uint32_t startBlock = topBlock - 100;
      if (topBlock < 100)
         startBlock = 0;
      bdmPtr_->applyBlockRangeToDB(startBlock, topBlock + 1, &sca);

      //grab merge lock
      while (mergeLock_.fetch_or(1, memory_order_acquire));

      scrAddrMap_.insert(scrAddrMapToMerge_.begin(), scrAddrMapToMerge_.end());

      UTxO_.insert(UTxOToMerge_.begin(), UTxOToMerge_.end());

      scrAddrMapToMerge_.clear();
      UTxOToMerge_.clear();

      mergeFlag_ = false;

      //release lock
      mergeLock_.store(0, memory_order_release);
   }
}


///////////////////////////////////////////////////////////////////////////////
//ZeroConfContainer Methods
///////////////////////////////////////////////////////////////////////////////
BinaryData ZeroConfContainer::getNewZCkey()
{
   uint32_t newId = topId_.fetch_add(1, memory_order_relaxed);
   BinaryData newKey = READHEX("ffff");
   newKey.append(WRITE_UINT32_BE(newId));

   return newKey;
}

///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::getTxByHash(const BinaryData& txHash, Tx& tx) const
{
   const auto keyIter = txHashToDBKey_.find(txHash);

   if (ITER_IN_MAP(keyIter, txHashToDBKey_))
   {
      tx = txMap_.find(keyIter->second)->second;
      return true;
   }

   return false;
}
///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::hasTxByHash(const BinaryData& txHash) const
{
   return (txHashToDBKey_.find(txHash) != txHashToDBKey_.end());
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::addRawTx(const BinaryData& rawTx, uint32_t txtime)
{
   /***
   Saves new ZC by txtime. txtime will always be unique, as it is grabbed
   locally and the protocol enforces a limit of 7 Tx per seconds, guaranteeing
   sufficient time granularity.
   ***/

   //convert raw ZC to a Tx object
   BinaryData ZCkey = getNewZCkey();
   Tx zcTx(rawTx);
   zcTx.setTxTime(txtime);

   //grab container lock
   while (lock_.fetch_or(1, memory_order_acquire));

   newZCMap_[ZCkey] = zcTx;

   //release lock
   lock_.store(0, memory_order_release);
}

///////////////////////////////////////////////////////////////////////////////
map<BinaryData, vector<BinaryData> > 
ZeroConfContainer::purge(LMDBBlockDatabase *db)
{
   map<BinaryData, vector<BinaryData> > invalidatedKeys;

   if (db == nullptr)
      return invalidatedKeys;

   /***
   When a new block appears, it will have added some ZC, but it also may
   invalidate other ZC, by adding a transcation that consumes the TxOut of one
   of our ZC (maleability is a good example).

   This would break a ZC chain starting off that one invalidated ZC,
   taking away the whole chain. The simpliest way to track down all
   invalidated ZC is to reparse them all, and compare the new list to the
   old one.

   For ZC chains to be parsed properly, it is important ZC transactions are
   parsed in the order they appeared.
   ***/
   SCOPED_TIMER("purgeZeroConfPool");

   map<HashString, HashString> txHashToDBKey;
   map<BinaryData, Tx>           txMap;
   map<HashString, map<BinaryData, TxIOPair> >  txioMap;

   //parse ZCs anew
   for (auto ZCPair : txMap_)
   {
      const BinaryData& txHash = ZCPair.second.getThisHash();

      if (scrAddrDataPtr_ != nullptr)
      {
         BinaryData ZCkey;

         auto keyIter = txHashToDBKey_.find(txHash);
         if (ITER_IN_MAP(keyIter, txHashToDBKey_))
            ZCkey = keyIter->second;
         else ZCkey = getNewZCkey();

         map<BinaryData, map<BinaryData, TxIOPair> > newTxIO =
            scrAddrDataPtr_->ZCisMineBulkFilter(ZCPair.second,
            ZCkey, db,
            ZCPair.second.getTxTime(),
            this);

         //if a relevant ZC was found, add it to our map
         if (newTxIO.size() > 0)
         {
            txHashToDBKey[txHash] = ZCkey;
            txMap[ZCPair.first] = ZCPair.second;

            for (const auto& scrAddrTxio : newTxIO)
            {
               auto& txioPair = txioMap[scrAddrTxio.first];

               txioPair.insert(scrAddrTxio.second.begin(),
                  scrAddrTxio.second.end());
            }
         }
      }
   }

   //intersect with current container map
   for (const auto& saMapPair : txioMap_)
   {
      auto saTxioIter = txioMap.find(saMapPair.first);
      if (saTxioIter == txioMap.end())
         continue;

      for (const auto& txioPair : saMapPair.second)
      {
         if (saTxioIter->second.find(txioPair.first) ==
            saTxioIter->second.end())
         {
            auto& txioVec = invalidatedKeys[saMapPair.first];
            txioVec.push_back(txioPair.first);
         }
      }
   }

   //copy new containers over
   txHashToDBKey_ = txHashToDBKey;
   txMap_ = txMap;
   txioMap_ = txioMap;

   //now purge newTxioMap_
   for (auto& newSaTxioPair : newTxioMap_)
   {
      auto validTxioIter = txioMap_.find(newSaTxioPair.first);

      if (ITER_NOT_IN_MAP(validTxioIter, txioMap_))
      {
         newSaTxioPair.second.clear();
         continue;
      }

      auto& validSaTxioMap = validTxioIter->second;
      auto& newSaTxioMap = newSaTxioPair.second;

      auto newTxioIter = newSaTxioMap.begin();

      while (newTxioIter != newSaTxioMap.end())
      {
         if (KEY_NOT_IN_MAP(newTxioIter->first, validSaTxioMap))
            newSaTxioMap.erase(newTxioIter++);
         else ++newTxioIter;
      }
   }

   return invalidatedKeys;

   /*
   // Rewrite the zero-conf pool file
   if (hashRmVec.size() > 0)
   rewriteZeroConfFile();
   */
}

///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::parseNewZC(LMDBBlockDatabase *db)
{
   /***
   ZC transcations are pushed to the BDM by another thread (usually the thread
   managing network connections). This is processed by addRawTx, which is meant
   to return fast. It grabs the container lock, inserts the new Tx object in
   the newZCMap_ and return, and sets the new ZC flag.

   The BDM main thread checks the ZC flag and calls this method. This method
   processes all new ZC and clears the newZCMap_. It checks how many ZC have
   been processed against the newZCMap_ size to make sure it can clear the map
   without deleting any new ZC that may have been added during the process.

   Note: there is no concurency interference with purging the container
   (for reorgs and new blocks), as they methods called by the BDM main thread.
   ***/
   uint32_t nProcessed = 0;

   bool zcIsOurs = false;

   //grab ZC container lock
   while (lock_.fetch_or(1, memory_order_acquire));

   //copy new ZC map
   map<BinaryData, Tx> zcMap = newZCMap_;

   //release lock
   lock_.store(0, memory_order_release);


   while (1)
   {
      for (const auto& newZCPair : zcMap)
      {
         nProcessed++;

         const BinaryData& txHash = newZCPair.second.getThisHash();
         if (txHashToDBKey_.find(txHash) != txHashToDBKey_.end())
            continue; //already have this ZC

         //LOGWARN << "new ZC transcation: " << txHash.toHexStr();

         if (scrAddrDataPtr_ != nullptr)
         {
            map<BinaryData, map<BinaryData, TxIOPair> > newTxIO =
               scrAddrDataPtr_->ZCisMineBulkFilter(newZCPair.second,
               newZCPair.first, db,
               newZCPair.second.getTxTime(),
               this);
            if (newTxIO.size() > 0)
            {
               txHashToDBKey_[txHash] = newZCPair.first;
               txMap_[newZCPair.first] = newZCPair.second;

               for (const auto& saTxio : newTxIO)
               {
                  auto& txioPair = txioMap_[saTxio.first];
                  txioPair.insert(saTxio.second.begin(),
                     saTxio.second.end());

                  auto& newTxioPair = newTxioMap_[saTxio.first];
                  newTxioPair.insert(saTxio.second.begin(),
                     saTxio.second.end());
               }

               zcIsOurs = true;
            }
         }
      }

      //grab ZC container lock
      while (lock_.fetch_or(1, memory_order_acquire));

      //check if newZCMap_ doesnt have new Txn
      if (nProcessed >= newZCMap_.size())
      {
         //clear map and release lock
         newZCMap_.clear();
         lock_.store(0, memory_order_release);

         //break out of the loop
         break;
      }

      //else search the new ZC container for unseen ZC
      map<BinaryData, Tx>::const_iterator newZcIter = newZCMap_.begin();

      while (newZcIter != newZCMap_.begin())
      {
         if (ITER_IN_MAP(zcMap.find(newZcIter->first), zcMap))
            newZCMap_.erase(newZcIter++);
         else
            ++newZcIter;
      }

      zcMap = newZCMap_;

      //reset counter and release lock
      lock_.store(0, memory_order_release);
      nProcessed = 0;
   }

   return zcIsOurs;
}

///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::getKeyForTxHash(const BinaryData& txHash,
   BinaryData zcKey) const
{
   const auto& hashPair = txHashToDBKey_.find(txHash);
   if (hashPair != txHashToDBKey_.end())
   {
      zcKey = hashPair->second;
      return true;
   }
   return false;
}

///////////////////////////////////////////////////////////////////////////////
map<HashString, map<BinaryData, TxIOPair> >
ZeroConfContainer::getNewTxioMap()
{
   //Copy zcTxioMap_, clear it and return the copy
   map<HashString, map<BinaryData, TxIOPair> > newZcTxioCopy = newTxioMap_;
   newTxioMap_.clear();

   return newZcTxioCopy;
}

