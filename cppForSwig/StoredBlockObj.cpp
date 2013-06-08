
/////////////////////////////////////////////////////////////////////////////
void StoredBlockHeader::setDuplicateID(uint8_t dupID)
{
   map<uint32_t, StoredTx>::iterator iter;
   for(iter  = txMap_.begin();
       iter != txMap_.end();
       iter++)
   {

   }
}

/////////////////////////////////////////////////////////////////////////////
bool StoredBlockHeader::haveFullBlock(void)
{
   if(!isInitialized || dataCopy_.getSize() != HEADER_SIZE)
      return false;

   for(uint32_t tx=0; tx<numTx_; tx++)
   {
      map<uint32_t, StoredTx>::iterator iter = txMap_.find(tx);
      if(iter == txMap_.end())
         return false;
      if(!iter->haveAllTxOut())
         return false;
   }

   return true;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredBlockHeader::getSerializedBlock(void)
{
   if(!haveFullBlock())
      return BinaryData(0);

   BinaryWriter bw;
   if(numBytes_>0)
      bw.reserve(numBytes_+100); // add extra room for header and var_int

   bw.put_BinaryData(dataCopy_); 
   bw.put_var_int(numTx_);
   for(uint32_t tx=0; tx<numTx_; tx++)
      bw.put_BinaryData(txMap_[tx].getSerializedTx());
   
   return bw.getData();
}


/////////////////////////////////////////////////////////////////////////////
void createFromBlockHeader(BlockHeader & bh)
{
   if(!bh.isInitialized())
   {
      Log::ERR() << "trying to create from uninitialized block header";
      return;
   } 

   unserialize(bh.serialize());

   numTx_ = bh.getNumTx();
   numBytes_ = bh.getBlockSize();
   blockHeight_ = bh.getBlockHeight();
   duplicateID_ = 0xff;
   isMainBranch_ = bh.isMainBranch();
}

/////////////////////////////////////////////////////////////////////////////
void unserialize(BinaryData & header80B);
{
   if(header80B.getSize() != HEADER_SIZE)
   {
      Log::ERR() << "Asked to unserialize a non-80-byte header";
      return;
   }
   dataCopy_.copyFrom(header80B);
   thisHash_ = BtcUtils::getHash256(header80B);
   isInitialized_ = true;
}

/////////////////////////////////////////////////////////////////////////////
void StoredBlockHeader::addTxToMap(uint32_t txIdx, Tx & tx)
{
   StoredTx storedtx;
   storedtx.createFromTx(tx);
   addTxToMap(txIdx, storedTx);
}

/////////////////////////////////////////////////////////////////////////////
void StoredBlockHeader::addTxToMap(uint32_t txIdx, StoredTx & tx)
{
      
}

/////////////////////////////////////////////////////////////////////////////
BlockHeader StoredBlockHeader::getBlocKHeaderCopy(void)
{
   if(!isInitialized)
      return BlockHeader(); 

   BlockHeader bh();
   bh.unserialize(dataCopy_);

   bh.setNumTx(numTx_);
   bh.setBlockSize(numBytes_);

   return bh;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredBlockHeader::getSerializedBlockHeader(void)
{
   if(!isInitialized)
      return BinaryData(0);

   return dataCopy_;
}


/////////////////////////////////////////////////////////////////////////////
void StoredBlockHeader::serializeForLDB(BinaryWriter & bw, 
                                        ARMORY_DB_TYPE dbType,
                                        DB_PRUNE_TYPE pruneType,
                                        MERKLE_SER_TYPE merkType=MERKLE_SER_FULL)
{
   if(!isInitialized_ || dataCopy_.getSize()==0)
   {
      Log::ERR() << " can't serialize an uninitialized header!";
      return;
   }

   if(merkType==MERKLE_SER_FULL && txMap_.size() < numTx_)
   {
      Log::ERR() << " Cannot produce full tx list";
      return;
   }
   
   //uint8_t version             =                   (flags & 0xf0000000) >> 28;
   //ARMORY_DB_TYPE dbtype       = (ARMORY_DB_TYPE)( (flags & 0x0f000000) >> 24);
   //DB_PRUNE_TYPE pruneType     = (DB_PRUNE_TYPE)(  (flags & 0x00c00000) >> 22);
   //MERKLE_SER_TYPE merkleCode  = (MERKLE_SER_TYPE)((flags & 0x00300000) >> 20);
   uint32_t flags = 0;
   flags |= ((uint32_t)ARMORY_DB_VERSION << 28) & 0xf0000000;
   flags |= ((uint32_t)dbType            << 24) & 0x0f000000;
   flags |= ((uint32_t)pruneType         << 22) & 0x00c00000;
   flags |= ((uint32_t)merkType          << 20) & 0x00300000;

   bw.put_uint32_t(flags);
   bw.put_BinaryData(dataCopy_);
   bw.put_uint32_t(numTx_);
   bw.put_uint32_t(numBytes_);

   if(merkType == MERKLE_SER_FULL)
   {
      map<uint32_t, StoredTx>::iterator iter = txMap_.begin();
      while(iter != txMap_.end())
         bw.put_BinaryData(iter->second.thisHash_)
   }
   else if(merkType == MERKLE_SER_PARTIAL)
   {
      vector<bool> isReqTx(numTx_);
      vector<HashString> reqTxs(numTx_);
      for(uint32_t tx=0; tx<numTx_; tx++)
      {
         isReqTx = false;
         reqTxs = BinaryData(0);
      }
      map<uint32_t, StoredTx>::iterator iter = txMap_.begin();
      while(iter != txMap_.end())
      {
         isReqTx[iter->first] = true;
         reqTxs[iter->first] = iter->second.thisHash_;
      }
      bw.put_BinaryData(PartialMerkleTree(numTx_, isReqTx, reqTxs).serialize());
   }
}

/////////////////////////////////////////////////////////////////////////////
bool StoredBlockHeader::serializeForHeaderDB(BinaryWriter & bw)
{
   if(!isInitialized_)
   {
      Log::ERR() << "Uninitialized Header";
      return false;
   }
   bw.put_BinaryData(dataCopy_);
   bw.put_uint32_t( heightAndDupToHgtx(blockHeight_, duplicateID_) );
}

/////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryDataRef data, bool fragged)
{
   unserialize(BinaryRefReader(data), fragged);
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryData const & data, bool fragged)
{
   unserialize(BinaryRefReader(data), fragged);
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryRefReader & brr, bool fragged)
{
   uint32_t numBytes = BtcUtils::StoredTxCalcLength( brr.getCurrPtr(), 
                                                     fragged,
                                                     &offsetsTxIn_, 
                                                     &offsetsTxOut_);
   dataCopy_.copyFrom(brr.getCurrPtr(), numBytes);

   isFragged_ = fragged;
   numTxOut_  = offsetsTxOut_.size()-1;
   version_   = *(uint32_t*)(ptr);
   lockTime_  = *(uint32_t*)(ptr + numBytes - 4);
   isInitialized_ = true;
}

////////////////////////////////////////////////////////////////////////////////
bool StoredTx::haveAllTxOut(void)
{
   if(!isInitialized_ || dataCopy_.getSize()==0)
      return false; 

   if(!isFragged_)
      return true;

   for(uint32_t i=0; i<numTxOut_; i++)
      if(txOutMap_.find(i) == txOutMap_.end())
         return false;

   return true;

}


////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTx::getSerializedTx(void)
{
   if(!isInitialized_)
      return BinaryData(0); 

   if(!isFragged_)
      return dataCopy_;
   else if(!haveAllTxOut())
      return BinaryData(0); 
    
   if(!isFragged_)
      return dataCopy_;

   BinaryWriter bw;
   if(numBytes_>0)
      bw.reserve(numBytes_);

   bw.put_BinaryData(dataCopy_.getPtr(), dataCopy_.getSize()-4);

   for(uint32_t txo=0; txo<numTxOut_; txo++)
      bw.put_BinaryData(txOutMap_[i].serialize());

   bw.put_BinaryData(dataCopy_.getPtr()+dataCopy_.getSize(), 4);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
Tx StoredTx::getTxCopy(void)
{
   Tx tx;
   tx.unserialize(getSerializedTx());
   return tx;
}


////////////////////////////////////////////////////////////////////////////////
void StoredTx::createFromTx(Tx & tx, bool doFrag)
{
   if(!tx.isInitialized())
   {
      Log::ERR() << "creating storedtx from uninitialized tx";
      isInitialized_ = false;
      return
   }

   thisHash_ = tx.getThisHash();
   numTxOut_ = tx.getNumTxOut();
   version_  = tx.getVersion();
   lockTime_ = tx.getLockTime(); 
   if(!doFrag)
   {
      isInitialized_ = true;
      isFragged_ = false;
      dataCopy_ = tx.serialize(); 
   }
   else
   {
      BinaryRefReader brr(tx.serialize());
      uint32_t firstOut  = tx.getTxOutOffset(0);
      uint32_t afterLast = tx.getTxOutOffset(numTxOut_);
      uint32_t span = afterLast - firstOut;
      dataCopy_.resize(tx.getSize() - span);
      brr.get_BinaryData(dataCopy_.getPtr(), firstOut);
      brr.advance(span);
      brr.get_BinaryData(dataCopy_.getPtr()+firstOut, 4);
   }
}
