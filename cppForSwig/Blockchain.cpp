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

#include "Blockchain.h"
#include "util.h"

#ifdef max
#undef max
#endif

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// Start Blockchain methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

Blockchain::Blockchain(const HashString &genesisHash)
   : genesisHash_(genesisHash)
{
   clear();
}

void Blockchain::clear()
{
   newlyParsedBlocks_.clear();
   headersByHeight_.resize(0);
   headersById_.clear();
   headerMap_.clear();
   headerMap_[genesisHash_] = make_shared<BlockHeader>();
   topBlockPtr_ = headerMap_[genesisHash_];
   topBlockId_ = 0;

   topID_.store(0, memory_order_relaxed);
}

void Blockchain::addBlock(
      const HashString &blockhash,
      const shared_ptr<BlockHeader> header,
      bool suppressVerbose
   )
{
   if (hasHeaderWithHash(blockhash) && blockhash != genesisHash_ &&
      !suppressVerbose)
   { // we don't show this error for the genesis block
      LOGWARN << "Somehow tried to add header that's already in map";
      LOGWARN << "    Header Hash: " << blockhash.copySwapEndian().toHexStr();
   }
   
   headerMap_[blockhash] = header;
   auto insertIter = headersById_.insert(make_pair(header->getThisID(), header));
   if (insertIter.second == false)
      LOGWARN << "block id duplicate: " << header->getThisID();
}

void Blockchain::addBlock(
   const HashString &blockhash,
   const shared_ptr<BlockHeader> header,
   uint32_t height, uint8_t dupId)
{
   addBlock(blockhash, header, false);
   header->blockHeight_ = height;
   header->duplicateID_ = dupId;

   auto&& bhID = header->getThisID();
   if (topID_.load(memory_order_relaxed) < bhID)
      topID_.store(bhID, memory_order_relaxed);
}

void Blockchain::addNewBlock(
   const HashString &blockhash,
   const shared_ptr<BlockHeader> header,
   bool suppressVerbose)
{
   addBlock(blockhash, header, suppressVerbose);
   newlyParsedBlocks_.push_back(header);
}

Blockchain::ReorganizationState Blockchain::organize(bool verbose)
{
   ReorganizationState st;
   st.prevTop_ = top();
   st.reorgBranchPoint_ = organizeChain(false, verbose);
   st.prevTopStillValid_ = (st.reorgBranchPoint_ == nullptr);
   st.hasNewTop_ = (st.prevTop_ != top());
   st.newTop_ = top();
   return st;
}

Blockchain::ReorganizationState Blockchain::forceOrganize()
{
   ReorganizationState st;
   st.prevTop_ = top();
   st.reorgBranchPoint_ = organizeChain(true);
   st.prevTopStillValid_ = (st.reorgBranchPoint_ == nullptr);
   st.hasNewTop_ = (st.prevTop_ != top());
   st.newTop_ = top();
   return st;
}

void Blockchain::setDuplicateIDinRAM(
   LMDBBlockDatabase* iface)
{
   for (const auto& block : headerMap_)
   {
      if (block.second->isMainBranch_)
         iface->setValidDupIDForHeight(
            block.second->blockHeight_, block.second->duplicateID_);
   }
}

Blockchain::ReorganizationState 
Blockchain::findReorgPointFromBlock(const BinaryData& blkHash)
{
   auto bh = getHeaderByHash(blkHash);
   
   ReorganizationState st;
   st.prevTop_ = bh;
   st.prevTopStillValid_ = true;
   st.hasNewTop_ = false;
   st.reorgBranchPoint_ = nullptr;

   while (!bh->isMainBranch())
   {
      BinaryData prevHash = bh->getPrevHash();
      bh = getHeaderByHash(prevHash);
   }

   if (bh != st.prevTop_)
   {
      st.reorgBranchPoint_ = bh;
      st.prevTopStillValid_ = false;
   }

   st.newTop_ = top();
   return st;
}

shared_ptr<BlockHeader> Blockchain::top() const
{
   return topBlockPtr_;
}

shared_ptr<BlockHeader> Blockchain::getGenesisBlock() const
{
   auto iter = headerMap_.find(genesisHash_);
   if (iter == headerMap_.end())
      throw runtime_error("missing genesis block header");

   return iter->second;
}

shared_ptr<BlockHeader> Blockchain::getHeaderByHeight(unsigned index)
{
   if(index>=headersByHeight_.size())
      throw std::range_error("Cannot get block at height " + to_string(index));

   return headersByHeight_[index];
}

const shared_ptr<BlockHeader> Blockchain::getHeaderByHeight(unsigned index) const
{
   auto headerIter = headersByHeight_.cbegin() + index;
   if (headerIter == headersByHeight_.cend())
      throw std::range_error("Cannot get block at height " + to_string(index));

   return (*headerIter);
}


bool Blockchain::hasHeaderByHeight(unsigned height) const
{
   if (height >= headersByHeight_.size())
      return false;

   return true;
}

const shared_ptr<BlockHeader> Blockchain::getHeaderByHash(HashString const & blkHash) const
{
   auto it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.copySwapEndian().toHexStr());
   else
      return it->second;
}
shared_ptr<BlockHeader> Blockchain::getHeaderByHash(HashString const & blkHash)
{
   auto it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.copySwapEndian().toHexStr());
   else
      return it->second;
}
shared_ptr<BlockHeader> Blockchain::getHeaderById(uint32_t id) const
{
   auto headerIter = headersById_.find(id);
   if (headerIter == headersById_.end())
   {
      LOGERR << "cannot find block for id: " << id;
      throw std::range_error("Cannot find block by id");
   }

   return headerIter->second;
}

bool Blockchain::hasHeaderWithHash(BinaryData const & txHash) const
{
   return KEY_IN_MAP(txHash, headerMap_);
}

const shared_ptr<BlockHeader> Blockchain::getHeaderPtrForTxRef(const TxRef &txr) const
{
   if(txr.isNull())
      throw std::range_error("Null TxRef");

   uint32_t hgt = txr.getBlockHeight();
   uint8_t  dup = txr.getDuplicateID();
   auto bh = getHeaderByHeight(hgt);
   if(bh->getDuplicateID() != dup)
   {
      throw runtime_error("Requested txref not on main chain (BH dupID is diff)");
   }
   return bh;
}

////////////////////////////////////////////////////////////////////////////////
// Returns nullptr if the new top block is a direct follower of
// the previous top. Returns the branch point if we had to reorg
// TODO:  Figure out if there is an elegant way to deal with a forked 
//        blockchain containing two equal-length chains
shared_ptr<BlockHeader> Blockchain::organizeChain(bool forceRebuild, bool verbose)
{
   if (verbose)
   {
      TIMER_START("orgChain");
      LOGINFO << "Organizing chain " << (forceRebuild ? "w/ rebuild" : "");
   }

   
   // If rebuild, we zero out any original organization data and do a 
   // rebuild of the chain from scratch.  This will need to be done in
   // the event that our first call to organizeChain returns false, which
   // means part of blockchain that was previously valid, has become
   // invalid.  Rather than get fancy, just rebuild all which takes less
   // than a second, anyway.
   if(forceRebuild)
   {
      map<HashString, shared_ptr<BlockHeader>>::iterator iter;
      for( iter  = headerMap_.begin(); 
           iter != headerMap_.end(); 
           iter++)
      {
         iter->second->difficultySum_  = -1;
         iter->second->blockHeight_ = 0;
         iter->second->isFinishedCalc_ = false;
         iter->second->nextHash_ = BtcUtils::EmptyHash();
         iter->second->isMainBranch_ = false;
      }
      topBlockPtr_ = NULL;
      topID_.store(0, memory_order_relaxed);
   }

   unsigned topID = topID_.load(memory_order_relaxed);

   // Set genesis block
   auto genBlock = getGenesisBlock();
   genBlock->blockHeight_ = 0;
   genBlock->difficultyDbl_ = 1.0;
   genBlock->difficultySum_ = 1.0;
   genBlock->isMainBranch_ = true;
   genBlock->isOrphan_ = false;
   genBlock->isFinishedCalc_ = true;
   genBlock->isInitialized_ = true;

   // If this is the first run, the topBlock is the genesis block
   auto topblock_iter = headersById_.find(topBlockId_);
   if (topblock_iter != headersById_.end())
   { 
      topBlockPtr_ = topblock_iter->second;
   }
   else
   {
      topBlockPtr_ = genBlock;
   }

   const auto prevTopBlock = top();
   
   // Iterate over all blocks, track the maximum difficulty-sum block
   double   maxDiffSum     = prevTopBlock->getDifficultySum();
   for( auto &header : values(headerMap_))
   {
      // *** Walk down the chain following prevHash fields, until
      //     you find a "solved" block.  Then walk back up and 
      //     fill in the difficulty-sum values (do not set next-
      //     hash ptrs, as we don't know if this is the main branch)
      //     Method returns instantly if block is already "solved"
      double thisDiffSum = traceChainDown(header);

      if (header->isOrphan_)
      {
         // disregard this block
      }
      // Determine if this is the top block.  If it's the same diffsum
      // as the prev top block, don't do anything
      else if(thisDiffSum > maxDiffSum)
      {
         maxDiffSum     = thisDiffSum;
         topBlockPtr_   = header;
         topBlockId_    = header->getThisID();
      }
   }

   
   // Walk down the list one more time, set nextHash fields
   // Also set headersByHeight_;
   bool prevChainStillValid = (topBlockPtr_ == prevTopBlock);
   topBlockPtr_->nextHash_ = BtcUtils::EmptyHash();
   auto thisHeaderPtr = topBlockPtr_;
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisHeaderPtr->isFinishedCalc_ )
   {
      thisHeaderPtr->isFinishedCalc_ = true;
      thisHeaderPtr->isMainBranch_   = true;
      thisHeaderPtr->isOrphan_       = false;
      headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

      if (thisHeaderPtr->uniqueID_ > topID)
         topID = thisHeaderPtr->uniqueID_;

      HashString & childHash    = thisHeaderPtr->thisHash_;
      thisHeaderPtr             = headerMap_[thisHeaderPtr->getPrevHash()];
      thisHeaderPtr->nextHash_  = childHash;

      if(thisHeaderPtr == prevTopBlock)
         prevChainStillValid = true;

   }
   // Last header in the loop didn't get added (the genesis block on first run)
   thisHeaderPtr->isMainBranch_ = true;
   headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

   topID_.store(topID + 1, memory_order_relaxed);

   // Force a full rebuild to make sure everything is marked properly
   // On a full rebuild, prevChainStillValid should ALWAYS be true
   if( !prevChainStillValid )
   {
      LOGWARN << "Reorg detected!";

      organizeChain(true); // force-rebuild blockchain (takes less than 1s)
      return thisHeaderPtr;
   }

   if (verbose)
   {
      TIMER_STOP("orgChain");
      auto duration = TIMER_READ_SEC("orgChain");
      LOGINFO << "Organized chain in " << duration << "s";
   }

   return 0;
}


/////////////////////////////////////////////////////////////////////////////
// Start from a node, trace down to the highest solved block, accumulate
// difficulties and difficultySum values.  Return the difficultySum of 
// this block.
double Blockchain::traceChainDown(shared_ptr<BlockHeader> bhpStart)
{
   if(bhpStart->difficultySum_ > 0)
      return bhpStart->difficultySum_;

   // Prepare some data structures for walking down the chain
   vector<shared_ptr<BlockHeader>>   headerPtrStack(headerMap_.size());
   vector<double>         difficultyStack(headerMap_.size());
   uint32_t blkIdx = 0;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   auto thisPtr = bhpStart;
   while( thisPtr->difficultySum_ < 0)
   {
      double thisDiff         = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      headerPtrStack[blkIdx]  = thisPtr;
      blkIdx++;

      auto iter = headerMap_.find(thisPtr->getPrevHash());
      if(ITER_IN_MAP(iter, headerMap_))
      {
         thisPtr = iter->second;
      }
      else
      {
         thisPtr->isOrphan_ = true;
         // this block is an orphan, possibly caused by a HeadersFirst
         // blockchain. Nothing to do about that
         return numeric_limits<double>::max();
      }
   }


   // Now we have a stack of difficulties and pointers.  Walk back up
   // (by pointer) and accumulate the difficulty values 
   double   seedDiffSum = thisPtr->difficultySum_;
   uint32_t blkHeight   = thisPtr->blockHeight_;
   for(int32_t i=blkIdx-1; i>=0; i--)
   {
      seedDiffSum += difficultyStack[i];
      blkHeight++;
      thisPtr                 = headerPtrStack[i];
      thisPtr->difficultyDbl_ = difficultyStack[i];
      thisPtr->difficultySum_ = seedDiffSum;
      thisPtr->blockHeight_   = blkHeight;
      thisPtr->isOrphan_ = false;
   }
   
   // Finally, we have all the difficulty sums calculated, return this one
   return bhpStart->difficultySum_;
  
}

/////////////////////////////////////////////////////////////////////////////
void Blockchain::putBareHeaders(LMDBBlockDatabase *db, bool updateDupID)
{
   /***
   Duplicated block heights (forks and orphans) have to saved to the headers
   DB.

   The current code detects the next unkown block by comparing the block
   hashes in the last parsed block file to the list saved in the DB. If
   the DB doesn't keep a record of duplicated or orphaned blocks, it will
   consider the next dup to be the first unknown block in DB until a new
   block file is created by Core.
   ***/
   for (auto& block : headerMap_)
   {
      StoredHeader sbh;
      sbh.createFromBlockHeader(*(block.second));
      uint8_t dup = db->putBareHeader(sbh, updateDupID);
      block.second->setDuplicateID(dup);  // make sure headerMap_ and DB agree
   }
}

/////////////////////////////////////////////////////////////////////////////
void Blockchain::putNewBareHeaders(LMDBBlockDatabase *db)
{
   unique_lock<mutex> lock(mu_);

   if (newlyParsedBlocks_.size() == 0)
      return;

   //create transaction here to batch the write
   LMDBEnv::Transaction tx;
   db->beginDBTransaction(&tx, HEADERS, LMDB::ReadWrite);

   vector<shared_ptr<BlockHeader>> unputHeaders;
   for (auto& block : newlyParsedBlocks_)
   {
      if (block->blockHeight_ != UINT32_MAX)
      {
         StoredHeader sbh;
         sbh.createFromBlockHeader(*block);
         //don't update SDBI, we'll do it here once instead
         uint8_t dup = db->putBareHeader(sbh, true, false);
         block->setDuplicateID(dup);  // make sure headerMap_ and DB agree
      }
      else
      {
         unputHeaders.push_back(block);
      }
   }

   //update SDBI, keep within the batch transaction
   auto&& sdbiH = db->getStoredDBInfo(HEADERS, 0);

   if (topBlockPtr_ == nullptr)
   {
      LOGINFO << "No known top block, didn't update SDBI";
      return;
   }

   if (topBlockPtr_->blockHeight_ >= sdbiH.topBlkHgt_)
   {
      sdbiH.topBlkHgt_ = topBlockPtr_->blockHeight_;
      sdbiH.topScannedBlkHash_ = topBlockPtr_->thisHash_;
      db->putStoredDBInfo(HEADERS, sdbiH, 0);
   }


   //once commited to the DB, they aren't considered new anymore, 
   //so clean up the container
   newlyParsedBlocks_ = unputHeaders;
}

/////////////////////////////////////////////////////////////////////////////
set<uint32_t> Blockchain::addBlocksInBulk(
   const map<HashString, shared_ptr<BlockHeader>>& bhMap)
{
   set<uint32_t> returnSet;
   unique_lock<mutex> lock(mu_);

   for (auto& header_pair : bhMap)
   {
      auto iter = headerMap_.insert(header_pair);
      if (!iter.second)
      {
         if (iter.first->second->dataCopy_.getSize() == HEADER_SIZE)
            continue;

         iter.first->second = header_pair.second;
      }

      headersById_[header_pair.second->getThisID()] = header_pair.second;
      newlyParsedBlocks_.push_back(header_pair.second);
      returnSet.insert(header_pair.second->getThisID());
   }

   return returnSet;
}

/////////////////////////////////////////////////////////////////////////////
void Blockchain::forceAddBlocksInBulk(
   const map<HashString, shared_ptr<BlockHeader>>& bhMap)
{
   unique_lock<mutex> lock(mu_);

   for (auto& headerPair : bhMap)
   {
      auto header = headerMap_[headerPair.first];
      header = headerPair.second;

      headersById_[header->getThisID()] = header;
      newlyParsedBlocks_.push_back(header);
   }
}

/////////////////////////////////////////////////////////////////////////////
map<unsigned, set<unsigned>> Blockchain::mapIDsPerBlockFile(void) const
{
   unique_lock<mutex> lock(mu_);

   map<unsigned, set<unsigned>> resultMap;

   for (auto& header : headersById_)
   {
      auto& result_set = resultMap[header.second->blkFileNum_];
      result_set.insert(header.second->uniqueID_);
   }

   return resultMap;
}

/////////////////////////////////////////////////////////////////////////////
map<unsigned, HeightAndDup> Blockchain::getHeightAndDupMap(void) const
{
   map<unsigned, HeightAndDup> hd_map;

   for (auto& block_pair : headersById_)
   {
      hd_map.insert(make_pair(
         block_pair.first,
         HeightAndDup(block_pair.second->getBlockHeight(),
                      block_pair.second->getDuplicateID())));
   }

   return hd_map;
}