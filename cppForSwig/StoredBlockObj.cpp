#include <vector>
#include <list>
#include <map>
#include "StoredBlockObj.h"

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::setParamsTrickle(uint32_t hgt,
                                    uint8_t  dupID,
                                    bool     isValid)
{
   // Set the params for this SBH object
   blockHeight_  = hgt;
   duplicateID_  = dupID;
   isMainBranch_ = isValid;

   // Then trickle down to each StoredTx object (if any)
   map<uint16_t, StoredTx>::iterator iter;     
   for(iter  = stxMap_.begin();
       iter != stxMap_.end();
       iter++)
   {
      iter->second.blockHeight_ = hgt;
      iter->second.blockDupID_  = dupID;

      // Trickle the data down to the TxOuts, too
      map<uint16_t, StoredTxOut>::iterator iter2; 
      for(iter2  = iter->second.stxoMap_.begin();
          iter2 != iter->second.stxoMap_.end();
          iter2++)
      {
         iter2->second.blockHeight_ = hgt;
         iter2->second.blockDupID_  = dupID; 
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
bool StoredHeader::haveFullBlock(void) const
{
   if(!isInitialized_ || dataCopy_.getSize() != HEADER_SIZE)
      return false;

   for(uint16_t tx=0; tx<numTx_; tx++)
   {
      map<uint16_t, StoredTx>::const_iterator iter = stxMap_.find(tx);
      if(iter == stxMap_.end())
         return false;
      if(!iter->second.haveAllTxOut())
         return false;
   }

   return true;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredHeader::getSerializedBlock(void) const
{
   if(!haveFullBlock())
      return BinaryData(0);

   BinaryWriter bw;
   if(numBytes_>0)
      bw.reserve(numBytes_+100); // add extra room for header and var_int

   bw.put_BinaryData(dataCopy_); 
   bw.put_var_int(numTx_);
   for(uint16_t tx=0; tx<numTx_; tx++)
      bw.put_BinaryData(stxMap_.at(tx).getSerializedTx());
   
   return bw.getData();
}



/////////////////////////////////////////////////////////////////////////////
void StoredHeader::createFromBlockHeader(BlockHeader & bh)
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
void StoredHeader::unserialize(BinaryData const & header80B)
{
   unserialize(header80B.getRef());
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::unserialize(BinaryRefReader brr)
{
   unserialize(brr.getRawRef());
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::unserialize(BinaryDataRef header80B)
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
void StoredHeader::unserializeFullBlock(BinaryRefReader brr, 
                                        bool doFrag,
                                        bool withPrefix)
{
   BinaryData magic;
   uint32_t   nBytes = UINT32_MAX;
   if(withPrefix)
   {
      magic  = brr.get_BinaryData(4);
      nBytes = brr.get_uint32_t();

      if(brr.getSizeRemaining() < nBytes)
      {
         Log::ERR() << "Not enough bytes remaining in BRR to read block";
         return;
      }
   }

   BlockHeader bh(brr); 
   uint32_t nTx = (uint32_t)brr.get_var_int();

   createFromBlockHeader(bh);
   numTx_ = nTx;
   numBytes_ = nBytes;
   if(dataCopy_.getSize() != HEADER_SIZE)
   {
      Log::ERR() << "Unserializing header did not produce 80-byte object!";
      return;
   }

   BtcUtils::getHash256(dataCopy_, thisHash_);

   for(uint32_t tx=0; tx<nTx; tx++)
   {
      // We're going to have to come back to the beginning of the tx, later
      uint32_t txStart = brr.getPosition();

      // Read a regular tx and then convert it
      Tx thisTx(brr);

      // Now add it to the map
      stxMap_[tx] = StoredTx();
      StoredTx & stx = stxMap_[tx];

      // Now copy the appropriate data from the vanilla Tx object
      stx.createFromTx(thisTx, doFrag);
      stx.blockHeight_   = UINT32_MAX;
      stx.blockDupID_    = UINT8_MAX;
      stx.isFragged_     = doFrag;
      stx.version_       = thisTx.getVersion();
      stx.txIndex_       = tx;
      stx.isInitialized_ = true;


      // Regardless of whether the tx is fragged, we still need the STXO map
      // to be updated and consistent
      brr.resetPosition();
      brr.advance(txStart + thisTx.getTxOutOffset(0));
      for(uint32_t txo=0; txo < thisTx.getNumTxOut(); txo++)
      {
         stx.stxoMap_[txo] = StoredTxOut();
         StoredTxOut & stxo = stx.stxoMap_[txo];

         stxo.unserialize(brr);
         stxo.txVersion_      = thisTx.getVersion();
         stxo.blockHeight_    = UINT32_MAX;
         stxo.blockDupID_     = UINT8_MAX;
         stxo.txIndex_        = tx;
         stxo.txOutIndex_     = txo;
         stxo.isFromCoinbase_ = thisTx.getTxIn(0).isCoinbase();
         stxo.isInitialized_  = true;
      }

      // Sitting at the nLockTime, 4 bytes before the end
      brr.advance(4);

      // Finally, add the 
      stxMap_[tx] = stx;
   }
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::unserializeFullBlock(BinaryDataRef block, 
                                        bool doFrag,
                                        bool withPrefix)
{
   BinaryRefReader brr(block);
   unserializeFullBlock(brr, doFrag, withPrefix);
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::addTxToMap(uint16_t txIdx, Tx & tx)
{
   StoredTx storedTx;
   storedTx.createFromTx(tx);
   addStoredTxToMap(txIdx, storedTx);
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::addStoredTxToMap(uint16_t txIdx, StoredTx & stx)
{
   stxMap_[txIdx] = stx; 
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::addTxOutToMap(uint16_t idx, TxOut & txout)
{
   StoredTxOut stxo;
   stxo.unserialize(txout.serialize());
   stxoMap_[idx] = stxo;
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::addStoredTxOutToMap(uint16_t idx, StoredTxOut & stxo)
{
   stxoMap_[idx] = stxo;
}

/////////////////////////////////////////////////////////////////////////////
BlockHeader StoredHeader::getBlockHeaderCopy(void) const
{
   if(!isInitialized_)
      return BlockHeader(); 

   BlockHeader bh(dataCopy_);

   bh.setNumTx(numTx_);
   bh.setBlockSize(numBytes_);

   return bh;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredHeader::getSerializedBlockHeader(void) const
{
   if(!isInitialized_)
      return BinaryData(0);

   return dataCopy_;
}


/////////////////////////////////////////////////////////////////////////////
/*
void StoredHeader::serializeForLDB(BinaryWriter & bw, 
                                   ARMORY_DB_TYPE dbType,
                                   DB_PRUNE_TYPE pruneType,
                                   MERKLE_SER_TYPE merkType=MERKLE_SER_FULL)
{
   if(!isInitialized_ || dataCopy_.getSize()==0)
   {
      Log::ERR() << " can't serialize an uninitialized header!";
      return;
   }

   if(merkType==MERKLE_SER_FULL && stxMap_.size() < numTx_)
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
      map<uint16_t, StoredTx>::iterator iter = stxMap_.begin();
      while(iter != stxMap_.end())
         bw.put_BinaryData(iter->second.thisHash_)
   }
   else if(merkType == MERKLE_SER_PARTIAL)
   {
      vector<bool> isReqTx(numTx_);
      vector<HashString> reqTxs(numTx_);
      for(uint16_t tx=0; tx<numTx_; tx++)
      {
         isReqTx = false;
         reqTxs = BinaryData(0);
      }
      map<uint16_t, StoredTx>::iterator iter = stxMap_.begin();
      while(iter != stxMap_.end())
      {
         isReqTx[iter->first] = true;
         reqTxs[iter->first] = iter->second.thisHash_;
      }
      bw.put_BinaryData(PartialMerkleTree(numTx_, isReqTx, reqTxs).serialize());
   }
}

/////////////////////////////////////////////////////////////////////////////
bool StoredHeader::serializeForHeaderDB(BinaryWriter & bw)
{
   if(!isInitialized_)
   {
      Log::ERR() << "Uninitialized Header";
      return false;
   }
   bw.put_BinaryData(dataCopy_);
   bw.put_uint32_t( heightAndDupToHgtx(blockHeight_, duplicateID_) );
}
*/


/////////////////////////////////////////////////////////////////////////////

/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryData const & data, bool fragged)
{
   BinaryRefReader brr(data);
   unserialize(brr, fragged);
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryDataRef data, bool fragged)
{
   BinaryRefReader brr(data);
   unserialize(brr, fragged);
}


/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserialize(BinaryRefReader & brr, bool fragged)
{
   vector<uint32_t> offsetsIn, offsetsOut; 
   uint32_t numBytes = BtcUtils::StoredTxCalcLength(brr.getCurrPtr(),
                                                    fragged,
                                                    &offsetsIn,
                                                    &offsetsOut);
   if(brr.getSizeRemaining() < numBytes)
   {
      Log::ERR() << "Not enough bytes in BRR to unserialize StoredTx";
      return;
   }

   brr.get_BinaryData(dataCopy_, numBytes);

   isFragged_ = fragged;
   numTxOut_  = offsetsOut.size()-1;
   version_   = *(uint32_t*)(dataCopy_.getPtr());
   lockTime_  = *(uint32_t*)(dataCopy_.getPtr() + numBytes - 4);
   isInitialized_ = true;
}



////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserialize(BinaryData const & data)
{
   BinaryRefReader brr(data);
   unserialize(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserialize(BinaryDataRef data)
{
   BinaryRefReader brr(data);
   unserialize(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserialize(BinaryRefReader & brr)
{
   if(brr.getSizeRemaining() < 8)
   {
      Log::ERR() << "Not enough bytes in BRR to unserialize StoredTxOut";
      return;
   }

   uint32_t numBytes = BtcUtils::TxOutCalcLength(brr.getCurrPtr());

   if(brr.getSizeRemaining() < numBytes)
   {
      Log::ERR() << "Not enough bytes in BRR to unserialize StoredTxOut";
      return;
   }

   brr.get_BinaryData(dataCopy_, numBytes);
   isInitialized_ = true;
}


////////////////////////////////////////////////////////////////////////////////
bool StoredTx::haveAllTxOut(void) const
{
   if(!isInitialized_ || dataCopy_.getSize()==0)
      return false; 

   if(!isFragged_)
      return true;

   for(uint16_t i=0; i<numTxOut_; i++)
      if(stxoMap_.find(i) == stxoMap_.end())
         return false;

   return true;

}


////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTx::getSerializedTx(void) const
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

   for(uint16_t txo=0; txo<numTxOut_; txo++)
      bw.put_BinaryData(stxoMap_.at(txo).getSerializedTxOut());

   bw.put_BinaryData(dataCopy_.getPtr()+dataCopy_.getSize()-4, 4);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxOut::getSerializedTxOut(void) const
{
   if(!isInitialized_)
      return BinaryData(0);

   return dataCopy_;
}

////////////////////////////////////////////////////////////////////////////////
Tx StoredTx::getTxCopy(void) const
{
   if(!haveAllTxOut())
   {
      Log::ERR() << "Cannot get tx copy, because don't have full StoredTx!";
      return Tx();
   }

   return Tx(getSerializedTx());
}


////////////////////////////////////////////////////////////////////////////////
StoredTx & StoredTx::createFromTx(Tx & tx, bool doFrag, bool withTxOuts)
{
   if(!tx.isInitialized())
   {
      Log::ERR() << "Creating storedtx from uninitialized tx. Aborting.";
      isInitialized_ = false;
      return *this;
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

   if(withTxOuts)
   {
      for(uint32_t txo = 0; txo < tx.getNumTxOut(); txo++)
      {
         stxoMap_[txo] = StoredTxOut();
         StoredTxOut & stxo = stxoMap_[txo];

         stxo.unserialize(tx.getTxOut(txo).serialize());
         stxo.txVersion_      = tx.getVersion();
         stxo.blockHeight_    = UINT32_MAX;
         stxo.blockDupID_     = UINT8_MAX;
         stxo.txIndex_        = tx.getBlockTxIndex();
         stxo.txOutIndex_     = txo;
         stxo.isFromCoinbase_ = tx.getTxIn(0).isCoinbase();
         stxo.isInitialized_  = true;
      }
   }

   return *this;
}


////////////////////////////////////////////////////////////////////////////////
StoredTxOut & StoredTxOut::createFromTxOut(TxOut & txout)
{
   unserialize(txout.serialize());
}







