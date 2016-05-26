////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
//                                                                            //
//  Copyright (C) 2016, goatpig                                               //            
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                   
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BDM_supportClasses.h"
#include "BlockUtils.h"
#include "txio.h"
#include <thread>


///////////////////////////////////////////////////////////////////////////////
//ScrAddrScanData Methods
///////////////////////////////////////////////////////////////////////////////

void ScrAddrFilter::getScrAddrCurrentSyncState()
{
   LMDBEnv::Transaction tx;
   lmdb_->beginDBTransaction(&tx, SSH, LMDB::ReadOnly);

   for (auto scrAddrPair : *scrAddrMap_)
      getScrAddrCurrentSyncState(scrAddrPair.first);
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::getScrAddrCurrentSyncState(
   BinaryData const & scrAddr)
{
   //grab ssh for scrAddr
   StoredScriptHistory ssh;
   lmdb_->getStoredScriptHistorySummary(ssh, scrAddr);

   //update scrAddrData lowest scanned block
   setScrAddrLastScanned(scrAddr, ssh.alreadyScannedUpToBlk_);
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::setSSHLastScanned(uint32_t height)
{
   LOGWARN << "Updating ssh last scanned";
   LMDBEnv::Transaction tx;
   lmdb_->beginDBTransaction(&tx, SSH, LMDB::ReadWrite);
   for (const auto scrAddrPair : *scrAddrMap_)
   {
      StoredScriptHistory ssh;
      lmdb_->getStoredScriptHistorySummary(ssh, scrAddrPair.first);
      if (!ssh.isInitialized())
         ssh.uniqueKey_ = scrAddrPair.first;

      ssh.alreadyScannedUpToBlk_ = height;

      lmdb_->putStoredScriptHistory(ssh);
   }
}

///////////////////////////////////////////////////////////////////////////////
bool ScrAddrFilter::registerAddresses(const set<BinaryData>& saSet, string ID,
   bool areNew, function<void(void)> callback)
{
   WalletInfo wltInfo;
   wltInfo.scrAddrSet_ = saSet;
   wltInfo.ID_ = ID;
   wltInfo.callback_ = callback;

   vector<WalletInfo> wltInfoVec;
   wltInfoVec.push_back(move(wltInfo));

   return registerAddressBatch(move(wltInfoVec), areNew);
}


///////////////////////////////////////////////////////////////////////////////
bool ScrAddrFilter::registerAddressBatch(
   vector<WalletInfo>&& wltInfoVec, bool areNew)
{
   /***
   return true if addresses were registered without the need for scanning
   ***/

   auto scraddrmapptr = scrAddrMap_;

   struct pred
   {
      shared_ptr<map<BinaryData, uint32_t>> saMap_;

      pred(shared_ptr<map<BinaryData, uint32_t>> saMap)
         : saMap_(saMap)
      {}

      bool operator()(WalletInfo& wltInfo) const
      {
         auto saIter = wltInfo.scrAddrSet_.begin();
         while (saIter != wltInfo.scrAddrSet_.end())
         {
            if (saMap_->find(*saIter) ==
               saMap_->end())
            {
               ++saIter;
               continue;
            }

            wltInfo.scrAddrSet_.erase(saIter++);
         }

         if (wltInfo.scrAddrSet_.size() == 0)
         {
            wltInfo.callback_();
            return false;
         }

         return true;
      }
   };
   
   auto removeIter = remove_if(wltInfoVec.begin(), wltInfoVec.end(), 
      pred(scraddrmapptr));
   wltInfoVec.erase(wltInfoVec.begin(), removeIter);
   
   if (wltInfoVec.size() == 0)
      return true;

   //check if the BDM is initialized. There ought to be a better way than
   //checking the top block
   if (bdmIsRunning())
   {
      //BDM is initialized and maintenance thread is running, check mode
      if (armoryDbType_ == ARMORY_DB_SUPER)
      {
         //supernode: nothing to do, signal the wallet that its scrAddr bulk 
         //is ready by passing isNew as true. Pass a blank BinaryData for the 
         //top scanned block hash in this case, it will be ignored anyways      
         
         throw runtime_error("needs reimplemented");

         for (auto& batch : wltInfoVec)
         {
            for (auto& sa : batch.scrAddrSet_)
               scraddrmapptr->insert(make_pair(sa, 0));
            batch.callback_();
         }

         scrAddrMap_ = scraddrmapptr;

         return true;
      }

      //create ScrAddrFilter for side scan         
      shared_ptr<ScrAddrFilter> sca = copy();
      sca->setParent(this);
      bool hasNewSA = false;

      if (areNew)
      {
         //mark addresses as fresh to skip DB scan
         doScan_ = false;
      }

      for (auto& batch : wltInfoVec)
      {
         if (batch.scrAddrSet_.size() == 0)
            continue;

         for (const auto& scrAddr : batch.scrAddrSet_)
            sca->regScrAddrForScan(scrAddr, 0);

         hasNewSA = true;
      }

      sca->buildSideScanData(wltInfoVec, areNew);
      scanFilterInNewThread(sca);

      if (!hasNewSA)
         return true;

      return false;
   }
   else
   {
      //BDM isnt initialized yet, the maintenance thread isnt running, 
      //just register the scrAddr and return true.
      for (auto& batch : wltInfoVec)
      {
         for (const auto& scrAddr : batch.scrAddrSet_)
            scrAddrMap_->insert(make_pair(scrAddr, 0));

         batch.callback_();
      }

      return true;
   }
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::scanScrAddrThread()
{
   //Only one wallet at a time         
   uint32_t endBlock = currentTopBlockHeight();
   vector<string> wltIDs = scrAddrDataForSideScan_.getWalletIDString();

   BinaryData topScannedBlockHash;
   {
      LMDBEnv::Transaction tx;
      lmdb_->beginDBTransaction(&tx, HEADERS, LMDB::ReadOnly);
      StoredHeader sbh;
      lmdb_->getBareHeader(sbh, endBlock);
      topScannedBlockHash = sbh.thisHash_;
   }

   if(doScan_ == false)
   {
      //new addresses, set their last seen block in the ssh entries
      setSSHLastScanned(currentTopBlockHeight());
   }
   else
   {
      //wipe ssh
      vector<BinaryData> saVec;
      for (const auto& scrAddrPair : *scrAddrMap_)
         saVec.push_back(scrAddrPair.first);
      wipeScrAddrsSSH(saVec);
      saVec.clear();

      //scan from 0
      topScannedBlockHash =
         applyBlockRangeToDB(0, endBlock, wltIDs);
   }
      
   addToMergePile(topScannedBlockHash);

   for (const auto& wID : wltIDs)
      LOGINFO << "Done with side scan of wallet " << wID;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::scanFilterInNewThread(shared_ptr<ScrAddrFilter> sca)
{
   auto scanMethod = [sca](void)->void
   { sca->scanScrAddrThread(); };

   thread scanThread(scanMethod);
   scanThread.detach();
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::addToMergePile(const BinaryData& lastScannedBlkHash)
{
   if (parent_ == nullptr)
      throw runtime_error("scf invalid parent");

   scrAddrDataForSideScan_.lastScannedBlkHash_ = lastScannedBlkHash;
   parent_->scanDataPile_.push_back(scrAddrDataForSideScan_);
   parent_->mergeSideScanPile();
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::mergeSideScanPile()
{
   /***
   We're about to add a set of newly registered scrAddrs to the BDM's
   ScrAddrFilter map. Make sure they are scanned up to the last known
   top block first, then merge it in.
   ***/

   vector<ScrAddrSideScanData> scanDataVec;
   map<BinaryData, uint32_t> newScrAddrMap;

   unique_lock<mutex> lock(mergeLock_);

   try
   {
      //pop all we can from the pile
      while (1)
         scanDataVec.push_back(move(scanDataPile_.pop_back()));
   }
   catch (IsEmpty&)
   {
      //pile is empty
   }

   if (scanDataVec.size() == 0)
      return;

   //prepare addresses for merging
   BlockHeader& lastScannedHeader =
      blockchain().getHeaderByHash(lastScannedHash_);

   BlockHeader lowestScanneHeader = lastScannedHeader;

   for (auto& scandata : scanDataVec)
   {
      for (auto& wltInfo : scandata.wltInfoVec_)
      {
         for (auto& sa : wltInfo.scrAddrSet_)
            newScrAddrMap.insert(make_pair(
               sa, lastScannedHeader.getBlockHeight()));
      }

      if (!scandata.doScan_)
         continue;

      //don't catch anything here, we want it to fail until handling
      //is implemented
      auto& header =
         blockchain().getHeaderByHash(scandata.lastScannedBlkHash_);

      //reimplement dealing with data scanned up to an orphaned top
      if (!header.isMainBranch())
         throw runtime_error("reimplement orphaned side scan error");

      if (lowestScanneHeader.getBlockHeight() > header.getBlockHeight())
         lowestScanneHeader = header;

   }

   //with the lowest common scanned header and all addresses in one
   //container, we can sync scan height for all addresses
   if (lowestScanneHeader.getThisHash() != lastScannedHash_)
   {
      //create sca
      auto newSca = copy();
      newSca->scrAddrMap_->insert(newScrAddrMap.begin(),
         newScrAddrMap.end());

      //scan them
      newSca->applyBlockRangeToDB(lowestScanneHeader.getBlockHeight(),
         lastScannedHeader.getBlockHeight(), vector<string>());
   }

   //add addresses to main filter map
   scrAddrMap_->insert(
      newScrAddrMap.begin(), newScrAddrMap.end());

   //write address merkle in SSH sdbi
   {
      auto&& addrMerkle = getAddressMapMerkle();

      StoredDBInfo sshSdbi;
      LMDBEnv::Transaction historytx;
      lmdb_->beginDBTransaction(&historytx, SSH, LMDB::ReadWrite);

      lmdb_->getStoredDBInfo(SSH, sshSdbi);
      sshSdbi.metaHash_ = addrMerkle;
      lmdb_->putStoredDBInfo(SSH, sshSdbi);
   }


   //hit callbacks
   for (auto& scandata : scanDataVec)
   {
      for (auto wltinfo : scandata.wltInfoVec_)
         wltinfo.callback_();
   }
}

///////////////////////////////////////////////////////////////////////////////
uint32_t ScrAddrFilter::scanFrom() const
{
   uint32_t lowestBlock = 0;

   if (scrAddrMap_->size())
   {
      lowestBlock = scrAddrMap_->begin()->second;

      for (auto scrAddr : *scrAddrMap_)
      {
         if (lowestBlock != scrAddr.second)
         {
            lowestBlock = 0;
            break;
         }
      }
   }

   if (lowestBlock != 0)
      lowestBlock++;

   return lowestBlock;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::clear()
{
   scanDataPile_.clear();
   for (auto& regScrAddr : *scrAddrMap_)
      regScrAddr.second = 0;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::buildSideScanData(const vector<WalletInfo>& wltInfoVec,
   bool areNew)
{
   scrAddrDataForSideScan_.startScanFrom_ = UINT32_MAX;
   for (const auto& scrAddrPair : *scrAddrMap_)
      scrAddrDataForSideScan_.startScanFrom_ = 
      min(scrAddrDataForSideScan_.startScanFrom_, scrAddrPair.second);

   scrAddrDataForSideScan_.wltInfoVec_ = wltInfoVec;
   scrAddrDataForSideScan_.doScan_ = !areNew;
}

///////////////////////////////////////////////////////////////////////////////
void ScrAddrFilter::getAllScrAddrInDB()
{
   LMDBEnv::Transaction tx;
   lmdb_->beginDBTransaction(&tx, SSH, LMDB::ReadOnly);
   auto dbIter = lmdb_->getIterator(SSH);   

   //iterate over ssh DB
   while(dbIter.advanceAndRead(DB_PREFIX_SCRIPT))
   {
      auto keyRef = dbIter.getKeyRef();
      StoredScriptHistory ssh;
      ssh.unserializeDBKey(dbIter.getKeyRef());
      ssh.unserializeDBValue(dbIter.getValueRef());

      (*scrAddrMap_)[ssh.uniqueKey_] = 0;
   } 

   for (auto scrAddrPair : *scrAddrMap_)
      getScrAddrCurrentSyncState(scrAddrPair.first);
}

///////////////////////////////////////////////////////////////////////////////
BinaryData ScrAddrFilter::getAddressMapMerkle(void) const
{
   vector<BinaryData> addrVec;
   addrVec.reserve(scrAddrMap_->size());
   for (auto& addrPair : *scrAddrMap_)
      addrVec.push_back(addrPair.first);

   if (addrVec.size() > 0)
      return BtcUtils::calculateMerkleRoot(addrVec);

   return BinaryData();
}

///////////////////////////////////////////////////////////////////////////////
bool ScrAddrFilter::hasNewAddresses(void) const
{
   if (scrAddrMap_->size() == 0)
      return false;

   //do not run before getAllScrAddrInDB
   auto&& currentmerkle = getAddressMapMerkle();
   BinaryData dbMerkle;

   {
      LMDBEnv::Transaction tx;
      lmdb_->beginDBTransaction(&tx, SSH, LMDB::ReadOnly);
      
      StoredDBInfo sdbi;
      lmdb_->getStoredDBInfo(SSH, sdbi);

      dbMerkle = sdbi.metaHash_;
   }

   if (dbMerkle == currentmerkle)
      return false;

   //merkles don't match, check height in each address
   auto scanfrom = scrAddrMap_->begin()->second;
   for (auto& scrAddrPair : *scrAddrMap_)
   {
      if (scanfrom != scrAddrPair.second)
         return true;
   }

   return false;
}

///////////////////////////////////////////////////////////////////////////////
//ZeroConfContainer Methods
///////////////////////////////////////////////////////////////////////////////
map<BinaryData, TxIOPair> ZeroConfContainer::emptyTxioMap_;

BinaryData ZeroConfContainer::getNewZCkey()
{
   uint32_t newId = topId_.fetch_add(1, memory_order_relaxed);
   BinaryData newKey = READHEX("ffff");
   newKey.append(WRITE_UINT32_BE(newId));

   return move(newKey);
}

///////////////////////////////////////////////////////////////////////////////
Tx ZeroConfContainer::getTxByHash(const BinaryData& txHash) const
{
   const auto keyIter = txHashToDBKey_.find(txHash);

   if (keyIter == txHashToDBKey_.end())
      return Tx();

   return txMap_.find(keyIter->second)->second;
}
///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::hasTxByHash(const BinaryData& txHash) const
{
   return (txHashToDBKey_.find(txHash) != txHashToDBKey_.end());
}

///////////////////////////////////////////////////////////////////////////////
set<BinaryData> ZeroConfContainer::purge()
{
   map<BinaryData, vector<BinaryData>> invalidatedKeys;

   if (!db_)
      return set<BinaryData>();

   /***
   For ZC chains to be parsed properly, it is important ZC transactions are
   parsed in the order they appeared.
   ***/
   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, ZERO_CONF, LMDB::ReadOnly);

   //get all txhashes for the new blocks
   set<BinaryData> minedHashes;
   auto bcPtr = db_->blockchain();
   try
   {
      const BlockHeader* lastKnownHeader =
         &bcPtr->getHeaderByHash(lastParsedBlockHash_);

      while (!lastKnownHeader->isMainBranch())
      {
         //trace back to the branch point
         auto&& bhash = lastKnownHeader->getPrevHash();
         lastKnownHeader = &bcPtr->getHeaderByHash(bhash);
      }

      //get the next header
      auto height = lastKnownHeader->getBlockHeight() + 1;
      lastKnownHeader = &bcPtr->getHeaderByHeight(height);

      while (lastKnownHeader != nullptr)
      {
         //grab block
         StoredHeader sbh;
         db_->getStoredHeader(sbh,
            lastKnownHeader->getBlockHeight(),
            lastKnownHeader->getDuplicateID(),
            false);

         //build up hash set
         for (auto& stx : sbh.stxMap_)
            minedHashes.insert(stx.second.thisHash_);

         //next block
         auto& bhash = lastKnownHeader->getNextHash();
         lastKnownHeader = &bcPtr->getHeaderByHash(bhash);
      }
   }
   catch (...)
   {
   }

   set<BinaryData> keysToDelete;

   //compare minedHashes to allZCTxHashes_
   for (auto& minedHash : minedHashes)
   {
      auto iter = allZcTxHashes_.find(minedHash);
      if (iter != allZcTxHashes_.end())
      {         
         auto zckeyIter = txHashToDBKey_.find(*iter);
         if (zckeyIter != txHashToDBKey_.end())
            keysToDelete.insert(zckeyIter->second);

         allZcTxHashes_.erase(iter);
      }
   }

   //reset containers
   txHashToDBKey_.clear();
   txMap_.clear();
   txioMap_.clear();
   keyToSpentScrAddr_.clear();
   txOutsSpentByZC_.clear();
   outPointsSpentByKey_.clear();

   return move(keysToDelete);
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::dropZC(const set<BinaryData>& txHashes)
{
   vector<BinaryData> keysToDelete;

   for (auto& hash : txHashes)
   {
      //resolve zcKey
      auto hashIter = txHashToDBKey_.find(hash);
      if (hashIter == txHashToDBKey_.end())
         continue;

      auto zcKey = hashIter->second;
      txHashToDBKey_.erase(hashIter);

      //drop from txMap_
      txMap_.erase(zcKey);

      //drop from keyToSpendScrAddr_
      auto&& scrAddrVec = keyToSpentScrAddr_[zcKey];
      keyToSpentScrAddr_.erase(zcKey);

      //drop from txioMap_
      for (auto& sa : scrAddrVec)
      {
         auto mapIter = txioMap_.find(sa);
         if (mapIter == txioMap_.end())
            continue;

         auto& txiomap = mapIter->second;

         auto txioIter = txiomap.begin();
         while (txioIter != txiomap.end())
         {
            if (txioIter->first.startsWith(sa))
               txiomap.erase(txioIter++);
            else
               ++txioIter;
         }
      }

      //drop from txOutsSpentByZC_
      auto txOutIter = txOutsSpentByZC_.begin();
      while (txOutIter != txOutsSpentByZC_.end())
      {
         if ((*txOutIter).startsWith(zcKey))
            txOutsSpentByZC_.erase(txOutIter++);
         else
            ++txOutIter;
      }

      //mark for deletion
      keysToDelete.push_back(zcKey);
   }

   //delete keys from DB
   auto deleteKeys = [&](void)->void
   {
      this->updateZCinDB(vector<BinaryData>(), keysToDelete);
   };

   thread deleteKeyThread(deleteKeys);
   if (deleteKeyThread.joinable())
      deleteKeyThread.join();
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::parseNewZC(void)
{
   while (1)
   {
      ZcActionStruct zcAction;
      map<BinaryData, Tx> zcMap;
      try
      {
         zcAction = move(newZcStack_.get());
      }
      catch (IsEmpty&)
      {
         break;
      }

      switch (zcAction.action_)
      {
      case Zc_Purge:
      {
         zcAction.zcMap_ = move(txMap_);
         auto&& keysToDelete = purge();
         auto keyIter = zcAction.zcMap_.begin();
         while (keyIter != zcAction.zcMap_.end())
         {
            if (keysToDelete.find(keyIter->first)
               != keysToDelete.end())
            {
               zcAction.zcMap_.erase(keyIter++);
            }
            else
               ++keyIter;
         }
      }

      case Zc_NewTx:
         zcMap = move(zcAction.zcMap_);
         break;

      case Zc_Shutdown:
         purge();
         return;

      default:
         continue;
      }

      set<BinaryData> newZcByHash;

      vector<BinaryData> keysToWrite, keysToDelete;

      for (auto& newZCPair : zcMap)
      {
         const BinaryData&& txHash = newZCPair.second.getThisHash();
         auto insertIter = allZcTxHashes_.insert(txHash);
         if (insertIter.second)
            keysToWrite.push_back(newZCPair.first);
      }

      auto waitonzcmap = waitOnZcMap_.get();

      for (auto& newZCPair : zcMap)
      {
         const BinaryData&& txHash = newZCPair.second.getThisHash();
         auto promiseIter = waitonzcmap->find(txHash);
         if (promiseIter != waitonzcmap->end())
            promiseIter->second->set_value(true);

         if (txHashToDBKey_.find(txHash) != txHashToDBKey_.end())
            continue; //already have this ZC

         //flag RBF on whole tx
         auto& zctx = newZCPair.second;
         zctx.setRBF(false);
         auto datacopy = zctx.getPtr();
         unsigned txinCount = zctx.getNumTxIn();

         for (unsigned i = 0; i < txinCount; i++)
         {
            BinaryDataRef consumedHash(datacopy + zctx.getTxInOffset(i), 32);
            auto hashiter = allZcTxHashes_.find(consumedHash);
            if (hashiter != allZcTxHashes_.end())
            {
               //a ZC spending a ZC output is marked as replaceable regardless
               //of sequence flagging
               zctx.setRBF(true);
               break;
            }
         }

         {
            auto&& bulkData =
               ZCisMineBulkFilter(newZCPair.second,
               newZCPair.first,
               newZCPair.second.getTxTime());

            //TODO: rework replacement by adding replaced tx to notification struct

            //check for replacement
            {
               //loop through all outpoints consumed by this ZC
               set<BinaryData> replacedHashes;
               for (auto& idSet : bulkData.outPointsSpentByKey_)
               {
                  //compare them to the list of currently spent outpoints
                  auto hashIter = outPointsSpentByKey_.find(idSet.first);
                  if (hashIter == outPointsSpentByKey_.end())
                     continue;

                  for (auto opId : idSet.second)
                  {
                     auto idIter = hashIter->second.find(opId.first);
                     if (idIter != hashIter->second.end())
                     {
                        //if 2 outpoints match, this ZC is replacing another
                        //flag the replaced key and clean up the entry
                        replacedHashes.insert(idSet.first);
                        hashIter->second.erase(idIter);
                     }
                  }
               }

               //drop the replacedKeys if any
               if (replacedHashes.size() > 0)
                  dropZC(replacedHashes);
            }

            //add ZC if its relevant
            if (!bulkData.isEmpty())
            {
               //merge spent outpoints
               txOutsSpentByZC_.insert(
                  bulkData.txOutsSpentByZC_.begin(),
                  bulkData.txOutsSpentByZC_.end());

               for (auto& idmap : bulkData.outPointsSpentByKey_)
               {
                  //cant use insert, have to replace values if they already exist
                  auto& thisIdMap = outPointsSpentByKey_[idmap.first];
                  for (auto& idpair : idmap.second)
                     thisIdMap[idpair.first] = idpair.second;
               }

               //merge new txios
               txHashToDBKey_[txHash] = newZCPair.first;
               txMap_[newZCPair.first] = newZCPair.second;

               //TODO: get rid of txioMap_, arrange by BDV and push to callbacks instead
               for (const auto& saTxio : bulkData.scrAddrTxioMap_)
               {
                  //again, can't use insert, have to overwrite existing data
                  auto& txioPair = txioMap_[saTxio.first];
                  for (auto txio : *saTxio.second)
                     txioPair[txio.first] = txio.second;
               }

               newZcByHash.insert(txHash);

               //notify BDVs
               auto bdvcallbacks = bdvCallbacks_.get();
               for (auto& bdvMap : bulkData.flaggedBDVs_)
               {
                  map<BinaryData, shared_ptr<map<BinaryData, TxIOPair>>>
                     notificationMap;
                  for (auto& sa : bdvMap.second)
                  {
                     auto saIter = bulkData.scrAddrTxioMap_.find(sa);
                     if (saIter == bulkData.scrAddrTxioMap_.end())
                        continue;

                     notificationMap.insert(*saIter);
                  }

                  auto callbackIter = bdvcallbacks->find(bdvMap.first);
                  if (callbackIter == bdvcallbacks->end())
                     continue;

                  callbackIter->second.newZcCallback_(move(notificationMap));
               }
            }
         }
      }

      {
         //write ZC in the new thread to guaranty we can get a RW tx
         auto writeNewZC = [&, this](void)->void
         { this->updateZCinDB(keysToWrite, keysToDelete); };

         thread writeNewZCthread(writeNewZC);
         writeNewZCthread.join();
      }
   
      lastParsedBlockHash_ = db_->getTopBlockHash();
   }
}

///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::getKeyForTxHash(const BinaryData& txHash,
   BinaryData& zcKey) const
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
ZeroConfContainer::BulkFilterData 
ZeroConfContainer::ZCisMineBulkFilter(const Tx & tx,
   const BinaryData & ZCkey, uint32_t txtime)
{
   // Since 99.999%+ of all transactions are not ours, let's do the 
   // fastest bulk filter possible, even though it will add 
   // redundant computation to the tx that are ours.  In fact,
   // we will skip the TxIn/TxOut convenience methods and follow the
   // pointers directly to the data we want

   /***filter is a pointer to a function that takes in a scrAddr (21 bytes,
   including the prefix) and returns a bool. For supernode, it should return
   true all the time.
   ***/

   auto bdvcallbacks = bdvCallbacks_.get();
   auto filter = [&bdvcallbacks](const BinaryData& addr)->set<string>
   {
      set<string> flaggedBDVs;

      for (auto& callbacks : *bdvcallbacks)
      {
         if (callbacks.second.addressFilter_(addr))
            flaggedBDVs.insert(callbacks.first);
      }

      return flaggedBDVs;
   };
   
   ZeroConfContainer::BulkFilterData bulkData;

   auto insertNewZc = [&bulkData](BinaryData sa,
      BinaryData txiokey, TxIOPair txio,
      set<string> flaggedBDVs)->void
   {
      bulkData.txOutsSpentByZC_.insert(txiokey);
      auto& key_txioPair = bulkData.scrAddrTxioMap_[sa];

      if (key_txioPair == nullptr)
         key_txioPair = make_shared<map<BinaryData, TxIOPair>>();

      (*key_txioPair)[txiokey] = move(txio);

      for (auto& bdvId : flaggedBDVs)
         bulkData.flaggedBDVs_[bdvId].insert(sa);
   };

   BinaryData txHash = tx.getThisHash();

   
   TxRef txref = db_->getTxRef(txHash);

   if (txref.isInitialized())
   {
      //Found this tx in the db. It is already part of a block thus 
      //is invalid as a ZC
      return bulkData;
   }

   bool isRBF = tx.isRBF();

   uint8_t const * txStartPtr = tx.getPtr();
   for (uint32_t iin = 0; iin<tx.getNumTxIn(); iin++)
   {
      OutPoint op;
      op.unserialize(txStartPtr + tx.getTxInOffset(iin), 36);

      //keep track of all outputs this ZC consumes
      auto& idSet = bulkData.outPointsSpentByKey_[op.getTxHash()];
      idSet.insert(make_pair(op.getTxOutIndex(), ZCkey));

      //check ZC txhash first, always cheaper than grabing a stxo from DB,
      //and will always be checked if the tx doesn't hit in DB outpoints.
      BinaryData opZcKey;
      if (getKeyForTxHash(op.getTxHash(), opZcKey))
      {
         TxRef outPointRef(opZcKey);
         uint16_t outPointId = op.getTxOutIndex();
         TxIOPair txio(outPointRef, outPointId,
            TxRef(ZCkey), iin);

         Tx chainedZC = getTxByHash(op.getTxHash());

         const TxOut& chainedTxOut = chainedZC.getTxOutCopy(outPointId);

         txio.setTxHashOfOutput(op.getTxHash());
         txio.setTxHashOfInput(txHash);

         txio.setValue(chainedTxOut.getValue());
         txio.setTxTime(txtime);
         txio.setRBF(chainedZC.isRBF());

         auto&& spentSA = chainedTxOut.getScrAddressStr();
         auto&& flaggedBDVs = filter(spentSA);

         auto&& txioKey = txio.getDBKeyOfOutput();
         insertNewZc(spentSA, move(txioKey), move(txio), move(flaggedBDVs));

         auto& wltIdVec = keyToSpentScrAddr_[ZCkey];
         wltIdVec.push_back(spentSA);

         continue;
      }


      //fetch the TxOut from DB
      DBOutPoint dbop(op, db_);
      auto&& opKey = dbop.getDBkey();
      if (opKey.getSize() == 8)
      {
         //found outPoint DBKey, grab the StoredTxOut
         StoredTxOut stxOut;
         if (db_->getStoredTxOut(stxOut, opKey))
         {
            if (stxOut.isSpent())
            {
               //invalid ZC, dump it
               return ZeroConfContainer::BulkFilterData();
            }

            BinaryData sa = stxOut.getScrAddress();
            auto&& flaggedBDVs = filter(sa);
            if (flaggedBDVs.size() > 0)
            {
               TxIOPair txio(
                  TxRef(opKey.getSliceRef(0, 6)), op.getTxOutIndex(),
                  TxRef(ZCkey), iin);

               txio.setTxHashOfOutput(op.getTxHash());
               txio.setTxHashOfInput(txHash);
               txio.setValue(stxOut.getValue());
               txio.setTxTime(txtime);
               txio.setRBF(isRBF);

               insertNewZc(sa, move(opKey), move(txio), move(flaggedBDVs));

               auto& wltIdVec = keyToSpentScrAddr_[ZCkey];
               wltIdVec.push_back(sa);
            }
         }
      }
   }

   // Simply convert the TxOut scripts to scrAddrs and check if registered
   for (uint32_t iout = 0; iout<tx.getNumTxOut(); iout++)
   {
      auto&& txout = tx.getTxOutCopy(iout);
      BinaryData scrAddr = txout.getScrAddressStr();
      auto&& flaggedBDVs = filter(scrAddr);
      if (flaggedBDVs.size() > 0)
      {
         TxIOPair txio(TxRef(ZCkey), iout);

         txio.setValue(txout.getValue());
         txio.setTxHashOfOutput(txHash);
         txio.setTxTime(txtime);
         txio.setUTXO(true);
         txio.setRBF(isRBF);

         auto&& txioKey = txio.getDBKeyOfOutput();
         insertNewZc(move(scrAddr), move(txioKey), 
            move(txio), move(flaggedBDVs));
      }
   }

   // If we got here, it's either non std or not ours
   return move(bulkData);
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::clear()
{
   txHashToDBKey_.clear();
   txMap_.clear();
   txioMap_.clear();
}

///////////////////////////////////////////////////////////////////////////////
bool ZeroConfContainer::isTxOutSpentByZC(const BinaryData& dbkey) 
   const
{
   if (txOutsSpentByZC_.find(dbkey) != txOutsSpentByZC_.end())
      return true;

   return false;
}

///////////////////////////////////////////////////////////////////////////////
const map<BinaryData, TxIOPair>& ZeroConfContainer::getZCforScrAddr(
   BinaryData scrAddr) const
{
   auto saIter = txioMap_.find(scrAddr);

   if (ITER_IN_MAP(saIter, txioMap_))
   {
      auto& zcMap = saIter->second;
      map<BinaryData, TxIOPair> returnMap;

      for (auto& zcPair : zcMap)
      {
         if (isTxOutSpentByZC(zcPair.second.getDBKeyOfOutput()))
            continue;

         returnMap.insert(zcPair);
      }

      return returnMap;
   }

   return emptyTxioMap_;
}

///////////////////////////////////////////////////////////////////////////////
const vector<BinaryData>& ZeroConfContainer::getSpentSAforZCKey(
   const BinaryData& zcKey) const
{
   auto iter = keyToSpentScrAddr_.find(zcKey);
   if (iter == keyToSpentScrAddr_.end())
      return emptyVecBinData_;

   return iter->second;
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::updateZCinDB(const vector<BinaryData>& keysToWrite, 
   const vector<BinaryData>& keysToDelete)
{
   //TODO: bulk writes

   //should run in its own thread to make sure we can get a write tx
   DB_SELECT dbs = ZERO_CONF;

   LMDBEnv::Transaction tx;
   db_->beginDBTransaction(&tx, dbs, LMDB::ReadWrite);

   for (auto& key : keysToWrite)
   {
      auto iter = txMap_.find(key);
      if (iter != txMap_.end())
      {
         StoredTx zcTx;
         zcTx.createFromTx(txMap_[key], true, true);
         db_->putStoredZC(zcTx, key);
      }
      else
      {
         //if the key is not to be found in the txMap_, this is a ZC txhash
         db_->putValue(ZERO_CONF, key, BinaryData());
      }
   }

   for (auto& key : keysToDelete)
   {
      BinaryData keyWithPrefix;
      if (key.getSize() == 6)
      {
         keyWithPrefix.resize(7);
         uint8_t* keyptr = keyWithPrefix.getPtr();
         keyptr[0] = DB_PREFIX_ZCDATA;
         memcpy(keyptr + 1, key.getPtr(), 6);
      }
      else
         keyWithPrefix = key;

      LDBIter dbIter(db_->getIterator(dbs));

      if (!dbIter.seekTo(keyWithPrefix))
         continue;

      vector<BinaryData> ktd;

      do
      {
         BinaryDataRef thisKey = dbIter.getKeyRef();
         if (!thisKey.startsWith(keyWithPrefix))
            break;

         ktd.push_back(thisKey);
      } 
      while (dbIter.advanceAndRead(DB_PREFIX_ZCDATA));

      for (auto Key : ktd)
         db_->deleteValue(dbs, Key);
   }
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::loadZeroConfMempool(bool clearMempool)
{
   map<BinaryData, Tx> zcMap;

   {
      auto dbs = ZERO_CONF;

      LMDBEnv::Transaction tx;
      db_->beginDBTransaction(&tx, dbs, LMDB::ReadOnly);
      LDBIter dbIter(db_->getIterator(dbs));

      if (!dbIter.seekToStartsWith(DB_PREFIX_ZCDATA))
      {
         enabled_ = true;
         return;
      }

      do
      {
         BinaryDataRef zcKey = dbIter.getKeyRef();

         if (zcKey.getSize() == 7)
         {
            //Tx, grab it from DB
            StoredTx zcStx;
            db_->getStoredZcTx(zcStx, zcKey);

            //add to newZCMap_
            auto&& zckey = zcKey.getSliceCopy(1, 6);
            Tx zctx(zcStx.getSerializedTx());
            zctx.setTxTime(zcStx.unixTime_);

            zcMap.insert(move(make_pair(
               move(zckey), move(zctx))));
         }
         else if (zcKey.getSize() == 9)
         {
            //TxOut, ignore it
            continue;
         }
         else if (zcKey.getSize() == 32)
         {
            //tx hash
            allZcTxHashes_.insert(zcKey);
         }
         else
         {
            //shouldn't hit this
            LOGERR << "Unknown key found in ZC mempool";
            break;
         }
      } while (dbIter.advanceAndRead(DB_PREFIX_ZCDATA));
   }

   if (clearMempool == true)
   {
      vector<BinaryData> keysToWrite, keysToDelete;

      for (const auto& zcTx : zcMap)
         keysToDelete.push_back(zcTx.first);

      updateZCinDB(keysToWrite, keysToDelete);
   }
   else if (zcMap.size())
   {   
      //set the zckey to the highest used index
      auto lastEntry = zcMap.end();
      auto& topZcKey = lastEntry->first;
      topId_.store(READ_UINT32_BE(topZcKey.getSliceCopy(2, 4)) +1);

      //push to parser stack
      ZcActionStruct actionstruct;
      actionstruct.setData(move(zcMap));
      actionstruct.action_ = Zc_NewTx;

      newZcStack_.push_back(move(actionstruct));
   }

   enabled_ = true;
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::init(
   function<bool(const BinaryData&)> zcFilter, bool clearMempool)
{
   loadZeroConfMempool(clearMempool);

   //start Zc parser thread
   auto processZcThread = [this](void)->void
   {
      parseNewZC();
   };

   thread parserThread(processZcThread);
   if (parserThread.joinable())
      parserThread.detach();

   //start invTx threads
   auto txthread = [this](void)->void
   {
      processInvTxThread();
   };

   for (int i = 0; i < GETZC_THREADCOUNT; i++)
   {
      thread thr(txthread);
      if (thr.joinable())
         thr.detach();
   }
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::processInvTxVec(vector<InvEntry> invVec)
{
   /***
   This code will ignore new tx if there are no threads ready in the thread
   pool to process them. Use a blocking stack instead to guarantee all
   new tx get processed.
   ***/

   for (auto& entry : invVec)
   {
      try
      {
         auto&& newtxpromise = newInvTxStack_.pop_front();
         newtxpromise.set_value(move(entry));
      }
      catch (IsEmpty&)
      {
         //nothing to do
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::processInvTxThread(void)
{
   while (1)
   {
      promise<InvEntry> newtxpromise;
      auto newtxfuture = newtxpromise.get_future();
      newInvTxStack_.push_back(move(newtxpromise));

      try
      {
         auto&& entry = newtxfuture.get();
         auto&& payload = networkNode_->getTx(entry);

         //push raw tx with current time
         pair<BinaryData, Tx> zcpair;
         zcpair.first = getNewZCkey();
         auto& rawTx = payload.getRawTx();
         zcpair.second.unserialize(&rawTx[0], rawTx.size());
         zcpair.second.setTxTime(time(0));

         ZcActionStruct actionstruct;
         actionstruct.zcMap_.insert(move(zcpair));
         actionstruct.action_ = Zc_NewTx;
         newZcStack_.push_back(move(actionstruct));
      }
      catch (BitcoinP2P_Exception&)
      {
         //ignore any p2p connection related exceptions
         continue;
      }
      catch (future_error&)
      {
         break;
      }
   }
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::insertBDVcallback(string id, BDV_Callbacks callback)
{
   bdvCallbacks_.insert(move(make_pair(move(id), move(callback))));
}

///////////////////////////////////////////////////////////////////////////////
void ZeroConfContainer::broadcastZC(const BinaryData& rawzc,
   uint32_t timeout_sec)
{
   //get tx hash
   auto&& txHash = BtcUtils::getHash256(rawzc);

   //create inv payload
   InvEntry entry;
   entry.invtype_ = Inv_Msg_Tx;
   memcpy(entry.hash, txHash.getPtr(), 32);
   
   vector<InvEntry> invVec;
   invVec.push_back(move(entry));

   Payload_Inv payload_inv;
   payload_inv.setInvVector(invVec);

   //create getData payload packet
   auto payload = make_unique<Payload_Tx>();
   vector<uint8_t> rawtx;
   rawtx.resize(rawzc.getSize());
   memcpy(&rawtx[0], rawzc.getPtr(), rawzc.getSize());

   payload->setRawTx(move(rawtx));
   auto getDataProm = make_shared<promise<bool>>();
   auto getDataFut = getDataProm->get_future();

   BitcoinP2P::getDataPayload getDataPayload;
   getDataPayload.payload_ = move(payload);
   getDataPayload.promise_ = getDataProm;

   pair<BinaryData, BitcoinP2P::getDataPayload> getDataPair;
   getDataPair.first = txHash;
   getDataPair.second = move(getDataPayload);

   //register getData payload
   networkNode_->getDataPayloadMap_.insert(move(getDataPair));

   //send inv packet
   networkNode_->sendMessage(move(payload_inv));

   //wait on getData future
   bool sentTx = false;
   if (timeout_sec == 0)
   {
      getDataFut.get();
      sentTx = true;
   }
   else
   {
      //auto getDataFutStatus = getDataFut.wait_for(chrono::seconds(timeout_sec));
      auto getDataFutStatus = getDataFut.wait_for(chrono::seconds(3000));
      if (getDataFutStatus == future_status::ready)
         sentTx = true;
   }

   networkNode_->getDataPayloadMap_.erase(txHash);

   if (!sentTx)
      throw runtime_error("broadcast tx timed out");

   //register tx hash for watching
   auto gotZcPromise = make_shared<promise<bool>>();
   auto watchTxFuture = gotZcPromise->get_future();
   waitOnZcMap_.insert(make_pair(txHash, gotZcPromise));

   //try to fetch tx by hash from node
   processInvTxVec(move(invVec));

   bool gotTx = false;
   if (timeout_sec == 0)
   {
      watchTxFuture.wait();
      gotTx = true;
   }
   else
   {
      auto status = watchTxFuture.wait_for(chrono::seconds(timeout_sec));
      if (status == future_status::ready)
         gotTx = true;
   }

   waitOnZcMap_.erase(txHash);

   if (!gotTx)
      throw runtime_error("broadcast tx timed out");
}
