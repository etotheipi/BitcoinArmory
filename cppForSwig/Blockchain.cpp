////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE or http://www.gnu.org/licenses/agpl.html                      //
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
   headerMap_.clear();
   topBlockPtr_ = genesisBlockBlockPtr_ =
      &headerMap_[genesisHash_];
}

BlockHeader& Blockchain::addBlock(
      const HashString &blockhash,
      const BlockHeader &block, 
      bool suppressVerbose
   )
{
   if (hasHeaderWithHash(blockhash) && blockhash != genesisHash_ &&
      !suppressVerbose)
   { // we don't show this error for the genesis block
      LOGWARN << "Somehow tried to add header that's already in map";
      LOGWARN << "    Header Hash: " << blockhash.copySwapEndian().toHexStr();
   }
   
   BlockHeader& bh = headerMap_[blockhash] = block;
   return bh;
}

BlockHeader& Blockchain::addBlock(
   const HashString &blockhash,
   const BlockHeader &block,
   uint32_t height, uint8_t dupId)
{
   BlockHeader& bh = addBlock(blockhash, block, false);
   bh.blockHeight_ = height;
   bh.duplicateID_ = dupId;

   return bh;
}

BlockHeader& Blockchain::addNewBlock(
   const HashString &blockhash,
   const BlockHeader &block,
   bool suppressVerbose)
{
   BlockHeader& bh = addBlock(blockhash, block, suppressVerbose);
   newlyParsedBlocks_.push_back(&bh);

   return bh;
}

Blockchain::ReorganizationState Blockchain::organize()
{
   ReorganizationState st;
   st.prevTopBlock = &top();
   st.reorgBranchPoint = organizeChain();
   st.prevTopBlockStillValid = !st.reorgBranchPoint;
   st.hasNewTop = (st.prevTopBlock != &top());
   return st;
}

Blockchain::ReorganizationState Blockchain::forceOrganize()
{
   ReorganizationState st;
   st.prevTopBlock = &top();
   st.reorgBranchPoint = organizeChain(true);
   st.prevTopBlockStillValid = !st.reorgBranchPoint;
   st.hasNewTop = (st.prevTopBlock != &top());
   return st;
}

void Blockchain::setDuplicateIDinRAM(
   LMDBBlockDatabase* iface, bool forceUpdateDupID)
{
   for (const auto& block : headerMap_)
   {
      if (block.second.isMainBranch_)
         iface->setValidDupIDForHeight(
            block.second.blockHeight_, block.second.duplicateID_);
   }
}

Blockchain::ReorganizationState 
Blockchain::findReorgPointFromBlock(const BinaryData& blkHash)
{
   BlockHeader *bh = &getHeaderByHash(blkHash);
   
   ReorganizationState st;
   st.prevTopBlock = bh;
   st.prevTopBlockStillValid = true;
   st.hasNewTop = false;
   st.reorgBranchPoint = nullptr;

   while (!bh->isMainBranch())
   {
      BinaryData prevHash = bh->getPrevHash();
      bh = &getHeaderByHash(prevHash);
   }

   if (bh != st.prevTopBlock)
   {
      st.reorgBranchPoint = bh;
      st.prevTopBlockStillValid = false;
   }

   return st;
}

BlockHeader& Blockchain::top() const
{
   return *topBlockPtr_;
}

BlockHeader& Blockchain::getGenesisBlock() const
{
   return *genesisBlockBlockPtr_;
}

BlockHeader& Blockchain::getHeaderByHeight(unsigned index) const
{
   if(index>=headersByHeight_.size())
      throw std::range_error("Cannot get block at height " + to_string(index));

   return *headersByHeight_[index];
}

bool Blockchain::hasHeaderByHeight(unsigned height) const
{
   if (height >= headersByHeight_.size())
      return false;

   return true;
}

const BlockHeader& Blockchain::getHeaderByHash(HashString const & blkHash) const
{
   map<HashString, BlockHeader>::const_iterator it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.copySwapEndian().toHexStr());
   else
      return it->second;
}
BlockHeader& Blockchain::getHeaderByHash(HashString const & blkHash)
{
   map<HashString, BlockHeader>::iterator it = headerMap_.find(blkHash);
   if(ITER_NOT_IN_MAP(it, headerMap_))
      throw std::range_error("Cannot find block with hash " + blkHash.copySwapEndian().toHexStr());
   else
      return it->second;
}

bool Blockchain::hasHeaderWithHash(BinaryData const & txHash) const
{
   return KEY_IN_MAP(txHash, headerMap_);
}

const BlockHeader& Blockchain::getHeaderPtrForTxRef(const TxRef &txr) const
{
   if(txr.isNull())
      throw std::range_error("Null TxRef");

   uint32_t hgt = txr.getBlockHeight();
   uint8_t  dup = txr.getDuplicateID();
   const BlockHeader& bh= getHeaderByHeight(hgt);
   if(bh.getDuplicateID() != dup)
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
BlockHeader* Blockchain::organizeChain(bool forceRebuild)
{
   SCOPED_TIMER("organizeChain");

   // Why did this line not through an error?  I left here to remind 
   // myself to go figure it out.
   //LOGINFO << ("Organizing chain", (forceRebuild ? "w/ rebuild" : ""));
   LOGDEBUG << "Organizing chain " << (forceRebuild ? "w/ rebuild" : "");

   
   // If rebuild, we zero out any original organization data and do a 
   // rebuild of the chain from scratch.  This will need to be done in
   // the event that our first call to organizeChain returns false, which
   // means part of blockchain that was previously valid, has become
   // invalid.  Rather than get fancy, just rebuild all which takes less
   // than a second, anyway.
   if(forceRebuild)
   {
      map<HashString, BlockHeader>::iterator iter;
      for( iter  = headerMap_.begin(); 
           iter != headerMap_.end(); 
           iter++)
      {
         iter->second.difficultySum_  = -1;
         iter->second.blockHeight_    =  0;
         iter->second.isFinishedCalc_ =  false;
         iter->second.nextHash_       =  BtcUtils::EmptyHash();
         iter->second.isMainBranch_   =  false;
      }
      topBlockPtr_ = NULL;
   }

   // Set genesis block
   BlockHeader & genBlock = getGenesisBlock();
   genBlock.blockHeight_    = 0;
   genBlock.difficultyDbl_  = 1.0;
   genBlock.difficultySum_  = 1.0;
   genBlock.isMainBranch_   = true;
   genBlock.isOrphan_       = false;
   genBlock.isFinishedCalc_ = true;
   genBlock.isInitialized_  = true; 

   // If this is the first run, the topBlock is the genesis block
   if(topBlockPtr_ == NULL)
      topBlockPtr_ = &genBlock;

   const BlockHeader& prevTopBlock = top();
   
   // Iterate over all blocks, track the maximum difficulty-sum block
   double   maxDiffSum     = prevTopBlock.getDifficultySum();
   for( BlockHeader &header : values(headerMap_))
   {
      // *** Walk down the chain following prevHash fields, until
      //     you find a "solved" block.  Then walk back up and 
      //     fill in the difficulty-sum values (do not set next-
      //     hash ptrs, as we don't know if this is the main branch)
      //     Method returns instantly if block is already "solved"
      double thisDiffSum = traceChainDown(header);

      if (header.isOrphan_)
      {
         // disregard this block
      }
      // Determine if this is the top block.  If it's the same diffsum
      // as the prev top block, don't do anything
      else if(thisDiffSum > maxDiffSum)
      {
         maxDiffSum     = thisDiffSum;
         topBlockPtr_   = &header;
      }
   }

   
   // Walk down the list one more time, set nextHash fields
   // Also set headersByHeight_;
   bool prevChainStillValid = (topBlockPtr_ == &prevTopBlock);
   topBlockPtr_->nextHash_ = BtcUtils::EmptyHash();
   BlockHeader* thisHeaderPtr = topBlockPtr_;
   //headersByHeight_.reserve(topBlockPtr_->getBlockHeight()+32768);
   headersByHeight_.resize(topBlockPtr_->getBlockHeight()+1);
   while( !thisHeaderPtr->isFinishedCalc_ )
   {
      thisHeaderPtr->isFinishedCalc_ = true;
      thisHeaderPtr->isMainBranch_   = true;
      thisHeaderPtr->isOrphan_       = false;
      headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;

      // This loop not necessary anymore with the DB implementation
      // We need to guarantee that the txs are pointing to the right block
      // header, because they could've been linked to an invalidated block
      //for(uint32_t i=0; i<thisHeaderPtr->getTxRefPtrList().size(); i++)
      //{
         //TxRef & tx = *(thisHeaderPtr->getTxRefPtrList()[i]);
         //tx.setHeaderPtr(thisHeaderPtr);
         //tx.setMainBranch(true);
      //}

      HashString & childHash    = thisHeaderPtr->thisHash_;
      thisHeaderPtr             = &(headerMap_[thisHeaderPtr->getPrevHash()]);
      thisHeaderPtr->nextHash_  = childHash;

      if(thisHeaderPtr == &prevTopBlock)
         prevChainStillValid = true;

   }
   // Last header in the loop didn't get added (the genesis block on first run)
   thisHeaderPtr->isMainBranch_ = true;
   headersByHeight_[thisHeaderPtr->getBlockHeight()] = thisHeaderPtr;


   // Force a full rebuild to make sure everything is marked properly
   // On a full rebuild, prevChainStillValid should ALWAYS be true
   if( !prevChainStillValid )
   {
      LOGWARN << "Reorg detected!";

      organizeChain(true); // force-rebuild blockchain (takes less than 1s)
      return thisHeaderPtr;
   }

   // Let the caller know that there was no reorg
   //LOGDEBUG << "Done organizing chain";
   return 0;
}


/////////////////////////////////////////////////////////////////////////////
// Start from a node, trace down to the highest solved block, accumulate
// difficulties and difficultySum values.  Return the difficultySum of 
// this block.
double Blockchain::traceChainDown(BlockHeader & bhpStart)
{
   if(bhpStart.difficultySum_ > 0)
      return bhpStart.difficultySum_;

   // Prepare some data structures for walking down the chain
   vector<BlockHeader*>   headerPtrStack(headerMap_.size());
   vector<double>         difficultyStack(headerMap_.size());
   uint32_t blkIdx = 0;

   // Walk down the chain of prevHash_ values, until we find a block
   // that has a definitive difficultySum value (i.e. >0). 
   BlockHeader* thisPtr = &bhpStart;
   while( thisPtr->difficultySum_ < 0)
   {
      double thisDiff         = thisPtr->difficultyDbl_;
      difficultyStack[blkIdx] = thisDiff;
      headerPtrStack[blkIdx]  = thisPtr;
      blkIdx++;

      map<HashString, BlockHeader>::iterator iter = headerMap_.find(thisPtr->getPrevHash());
      if(ITER_IN_MAP(iter, headerMap_))
      {
         thisPtr = &(iter->second);
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
   return bhpStart.difficultySum_;
  
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
      sbh.createFromBlockHeader(block.second);
      uint8_t dup = db->putBareHeader(sbh, updateDupID);
      block.second.setDuplicateID(dup);  // make sure headerMap_ and DB agree
   }
}

/////////////////////////////////////////////////////////////////////////////
void Blockchain::putNewBareHeaders(LMDBBlockDatabase *db)
{
   for (auto& block : newlyParsedBlocks_)
   {
      StoredHeader sbh;
      sbh.createFromBlockHeader(*block);
      uint8_t dup = db->putBareHeader(sbh, true);
      block->setDuplicateID(dup);  // make sure headerMap_ and DB agree
   }

   //once commited to the DB, they aren't considered new anymore, 
   //so clean up the container
   newlyParsedBlocks_.clear();
}
