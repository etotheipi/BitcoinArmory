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
void StoredHeader::setHeightAndDup(uint32_t hgt, uint8_t dupID)
{
   blockHeight_ = hgt;
   duplicateID_ = dupID;
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::setHeightAndDup(BinaryData hgtx)
{
   blockHeight_ = ARMDB.hgtxToHeight(hgtx);
   duplicateID_ = ARMDB.hgtxToDupID(hgtx);
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
      LOGERR << "trying to create from uninitialized block header";
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
      LOGERR << "Asked to unserialize a non-80-byte header";
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
         LOGERR << "Not enough bytes remaining in BRR to read block";
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
      LOGERR << "Unserializing header did not produce 80-byte object!";
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
      stx.createFromTx(thisTx, doFrag, true);
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
         stxo.isCoinbase_     = thisTx.getTxIn(0).isCoinbase();
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
bool StoredHeader::serializeFullBlock(BinaryWriter & bw) const
{
   if(!haveFullBlock())
   {
      LOGERR << "Attempted to serialize full block, but only have partial";
      return false;
   }

   if(numTx_ == UINT32_MAX)
   {
      LOGERR << "Number of tx not available while serializing full block";
      return false;
   }

   BinaryWriter bwTemp(1024*1024); // preallocate 1 MB which is the limit
   bwTemp.put_BinaryData(dataCopy_);
   bwTemp.put_var_int(numTx_);
   map<uint16_t, StoredTx>::const_iterator iter;
   for(iter = stxMap_.begin(); iter != stxMap_.end(); iter++)
   {
      if(!iter->second.haveAllTxOut())
      {
         LOGERR << "Don't have all TxOut in tx during serialize full block";
         return false;
      }
      bwTemp.put_BinaryData(iter->second.getSerializedTx());
   }
   
   bw.put_BinaryData(bwTemp.getDataRef());
   return true;
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
   if(txIdx >= numTx_)
   {
      LOGERR << "TxIdx is greater than numTx of stored header";
      return;
   }
   stxMap_[txIdx] = stx; 
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::addTxOutToMap(uint16_t idx, TxOut & txout)
{
   if(idx >= numTxOut_)
   {
      LOGERR << "TxOutIdx is greater than numTxOut of stored tx";
      return;
   }
   StoredTxOut stxo;
   stxo.unserialize(txout.serialize());
   stxoMap_[idx] = stxo;
}

/////////////////////////////////////////////////////////////////////////////
void StoredTx::addStoredTxOutToMap(uint16_t idx, StoredTxOut & stxo)
{
   if(idx >= numTxOut_)
   {
      LOGERR << "TxOutIdx is greater than numTxOut of stored tx";
      return;
   }
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
void StoredHeader::unserializeDBValue( DB_SELECT         db,
                                       BinaryRefReader & brr,
                                       bool              ignoreMerkle)
{

   if(db==HEADERS)
   {
      brr.get_BinaryData(dataCopy_, HEADER_SIZE);
      BinaryData hgtx = brr.get_BinaryData(4);
      blockHeight_ = ARMDB.hgtxToHeight(hgtx);
      duplicateID_ = ARMDB.hgtxToDupID(hgtx);
   }
   else if(db==BLKDATA)
   {
      // Read the flags byte
      BitUnpacker<uint32_t> bitunpack(brr);
      unserArmVer_        =                  bitunpack.getBits(4);
      unserBlkVer_        =                  bitunpack.getBits(4);
      unserDbType_        = (ARMORY_DB_TYPE) bitunpack.getBits(4);
      unserPrType_        = (DB_PRUNE_TYPE)  bitunpack.getBits(2);
      unserMkType_        = (MERKLE_SER_TYPE)bitunpack.getBits(2);
   
      // Unserialize the raw header into the SBH object
      brr.get_BinaryData(dataCopy_, HEADER_SIZE);
      numTx_    = brr.get_uint32_t();
      numBytes_ = brr.get_uint32_t();

      if(unserArmVer_ != ARMORY_DB_VERSION)
         LOGWARN << "Version mismatch in unserialize DB header";

      if( !ignoreMerkle )
      {
         uint32_t currPos = brr.getPosition();
         uint32_t totalSz = brr.getSize();
         if(unserMkType_ == MERKLE_SER_NONE)
            merkle_.resize(0);
         else
         {
            merkleIsPartial_ = (unserMkType_ == MERKLE_SER_PARTIAL);
            brr.get_BinaryData(merkle_, totalSz - currPos);
         }
      }
   }

}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::serializeDBValue( DB_SELECT       db,
                                     BinaryWriter &  bw) const
{
   if(!isInitialized_)
   {
      LOGERR << "Attempted to serialize uninitialized block header";
      return;
   }

   if(db==HEADERS)
   {
      BinaryData hgtx = ARMDB.heightAndDupToHgtx(blockHeight_, duplicateID_);
      bw.put_BinaryData(dataCopy_);
      bw.put_BinaryData(hgtx);
   }
   else if(db==BLKDATA)
   {
      uint32_t version = READ_UINT32_LE(dataCopy_.getPtr());

      // TODO:  We define merkle serialization types here, but we're not actually
      //        enforcing it in this function.  Either merkle_ member contains 
      //        the correct form of the merkle data or it doesn't.  We should 
      //        figure out whether we need to make sure the correct data is 
      //        already here when this function starts, or guarantee the data
      //        is in the right form as part of this function.  For now I'm 
      //        assuming that it's already in the right form, and thus the
      //        determination of PARTIAL vs FULL is irrelevant
      MERKLE_SER_TYPE mtype;
      switch(ARMDB.getArmoryDbType())
      {
         // If we store all the tx anyway, don't need any/partial merkle trees
         case ARMORY_DB_LITE:    mtype = MERKLE_SER_PARTIAL; break;
         case ARMORY_DB_PARTIAL: mtype = MERKLE_SER_FULL;    break;
         case ARMORY_DB_FULL:    mtype = MERKLE_SER_NONE;    break;
         case ARMORY_DB_SUPER:   mtype = MERKLE_SER_NONE;    break;
         default: 
            LOGERR << "Invalid DB mode in serializeStoredHeaderValue";
      }
      
      // Override the above mtype if the merkle data is zero-length
      if(merkle_.getSize()==0)
         mtype = MERKLE_SER_NONE;
   
      // Create the flags byte
      BitPacker<uint32_t> bitpack;
      bitpack.putBits((uint32_t)ARMORY_DB_VERSION,       4);
      bitpack.putBits((uint32_t)version,                 4);
      bitpack.putBits((uint32_t)ARMDB.getArmoryDbType(), 4);
      bitpack.putBits((uint32_t)ARMDB.getDbPruneType(),  2);
      bitpack.putBits((uint32_t)mtype,                   2);

      bw.put_BitPacker(bitpack);
      bw.put_BinaryData(dataCopy_);
      bw.put_uint32_t(numTx_);
      bw.put_uint32_t(numBytes_);

      if( mtype != MERKLE_SER_NONE )
      {
         bw.put_BinaryData(merkle_);
         if(merkle_.getSize()==0)
            LOGERR << "Expected to serialize merkle tree, but empty string";
      }
   }
}


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
   uint32_t nbytes = BtcUtils::StoredTxCalcLength(brr.getCurrPtr(),
                                                  fragged,
                                                  &offsetsIn,
                                                  &offsetsOut);
   if(brr.getSizeRemaining() < nbytes)
   {
      LOGERR << "Not enough bytes in BRR to unserialize StoredTx";
      return;
   }

   brr.get_BinaryData(dataCopy_, nbytes);

   isFragged_ = fragged;
   numTxOut_  = offsetsOut.size()-1;
   version_   = READ_UINT32_LE(dataCopy_.getPtr());
   lockTime_  = READ_UINT32_LE(dataCopy_.getPtr() + nbytes - 4);
   isInitialized_ = true;

   if(isFragged_)
   {
      fragBytes_ = nbytes;
      numBytes_ = UINT32_MAX;
   }
   else
   {
      numBytes_ = nbytes;
      uint32_t span = offsetsOut[numTxOut_] - offsetsOut[0];
      fragBytes_ = numBytes_ - span;
      thisHash_ = BtcUtils::getHash256(dataCopy_);
   }
}





/////////////////////////////////////////////////////////////////////////////
void StoredTx::unserializeDBValue(BinaryRefReader & brr)
{
   // flags
   //    DBVersion      4 bits
   //    TxVersion      2 bits
   //    HowTxSer       4 bits   (FullTxOut, TxNoTxOuts, numTxOutOnly)
   BitUnpacker<uint16_t> bitunpack(brr); // flags
   unserArmVer_  =                    bitunpack.getBits(4);
   unserTxVer_   =                    bitunpack.getBits(2);
   unserTxType_  = (TX_SERIALIZE_TYPE)bitunpack.getBits(4);

   if(unserArmVer_ != ARMORY_DB_VERSION)
      LOGWARN << "Version mismatch in unserialize DB tx";
   
   brr.get_BinaryData(thisHash_, 32);

   if(unserTxType_ == TX_SER_FULL || unserTxType_ == TX_SER_FRAGGED)
      unserialize(brr, unserTxType_==TX_SER_FRAGGED);
   else
      numTxOut_ = brr.get_var_int();
}


/////////////////////////////////////////////////////////////////////////////
void StoredTx::serializeDBValue(BinaryWriter & bw) const
{
   TX_SERIALIZE_TYPE serType;
   
   switch(ARMDB.getArmoryDbType())
   {
      // In most cases, if storing separate TxOuts, fragged Tx is fine
      case ARMORY_DB_LITE:    serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_PARTIAL: serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_FULL:    serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_SUPER:   serType = TX_SER_FULL;    break;
      default: 
         LOGERR << "Invalid DB mode in serializeStoredTxValue";
   }

   if(serType==TX_SER_FULL && !haveAllTxOut())
   {
      LOGERR << "Supposed to write out full Tx, but don't have it";
      return;
   }

   if(thisHash_.getSize() == 0)
   {
      LOGERR << "Do not know tx hash to be able to DB-serialize StoredTx";
      return;
   }

   uint16_t version = (uint16_t)READ_UINT32_LE(dataCopy_.getPtr());

   BitPacker<uint16_t> bitpack;
   bitpack.putBits((uint16_t)ARMORY_DB_VERSION,  4);
   bitpack.putBits((uint16_t)version,            2);
   bitpack.putBits((uint16_t)serType,            4);

   
   bw.put_BitPacker(bitpack);
   bw.put_BinaryData(thisHash_);

   if(serType == TX_SER_FULL)
      bw.put_BinaryData(getSerializedTx());
   else if(serType == TX_SER_FRAGGED)
      bw.put_BinaryData(getSerializedTxFragged());
   else
      bw.put_var_int(numTxOut_);
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
    
   if(numBytes_ == UINT32_MAX)
   {
      LOGERR << "Do not know size of tx in order to serialize it";
      return BinaryData(0);
   }

   BinaryWriter bw;
   bw.reserve(numBytes_);
   bw.put_BinaryData(dataCopy_.getPtr(), dataCopy_.getSize()-4);

   map<uint16_t, StoredTxOut>::const_iterator iter;
   uint16_t i=0;
   for(iter = stxoMap_.begin(); iter != stxoMap_.end(); iter++, i++)
   {
      if(iter->first != i)
      {
         LOGERR << "Indices out of order accessing stxoMap_...?!";
         return BinaryData(0);
      }
      bw.put_BinaryData(iter->second.getSerializedTxOut());
   }

   bw.put_BinaryData(dataCopy_.getPtr()+dataCopy_.getSize()-4, 4);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTx::getSerializedTxFragged(void) const
{
   if(!isInitialized_)
      return BinaryData(0); 

   if(isFragged_)
      return dataCopy_;

   if(numBytes_ == UINT32_MAX)
   {
      LOGERR << "Do not know size of tx in order to serialize it";
      return BinaryData(0);
   }

   BinaryWriter bw;
   vector<uint32_t> outOffsets;
   BtcUtils::StoredTxCalcLength(dataCopy_.getPtr(), false, NULL, &outOffsets);
   uint32_t firstOut  = outOffsets[0];
   uint32_t afterLast = outOffsets[outOffsets.size()-1];
   uint32_t span = afterLast - firstOut;

   BinaryData output(dataCopy_.getSize() - span);
   dataCopy_.getSliceRef(0,  firstOut).copyTo(output.getPtr());
   dataCopy_.getSliceRef(afterLast, 4).copyTo(output.getPtr()+firstOut);
   return output;
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
      LOGERR << "Not enough bytes in BRR to unserialize StoredTxOut";
      return;
   }

   uint32_t numBytes = BtcUtils::TxOutCalcLength(brr.getCurrPtr());

   if(brr.getSizeRemaining() < numBytes)
   {
      LOGERR << "Not enough bytes in BRR to unserialize StoredTxOut";
      return;
   }

   brr.get_BinaryData(dataCopy_, numBytes);
   isInitialized_ = true;
}



////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserializeDBValue(BinaryRefReader & brr)
{
   // Similar to TxValue flags
   //    DBVersion   4 bits
   //    TxVersion   2 bits
   //    Spentness   2 bits
   BitUnpacker<uint16_t> bitunpack(brr);
   unserArmVer_ =                  bitunpack.getBits(4);
   txVersion_   =                  bitunpack.getBits(2);
   spentness_   = (TXOUT_SPENTNESS)bitunpack.getBits(2);
   isCoinbase_  =                  bitunpack.getBits(1);

   unserialize(brr);
   if(spentness_ == TXOUT_SPENT && brr.getSizeRemaining()>=8)
      spentByTxInKey_ = brr.get_BinaryData(8); 

}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::serializeDBValue(BinaryWriter & bw,
                                   bool forceSaveSpentness) const
{
   TXOUT_SPENTNESS writeSpent = spentness_;
   
   if(!forceSaveSpentness)
   { 
      switch(ARMDB.getArmoryDbType())
      {
         //// If the DB is in lite or partial modes, we don't bother recording
         //   spentness (in fact, if it's spent, this entry probably won't even
         //   be written to the DB).
         case ARMORY_DB_LITE:    writeSpent = TXOUT_SPENTUNK; break;
         case ARMORY_DB_PARTIAL: writeSpent = TXOUT_SPENTUNK; break;
         case ARMORY_DB_FULL:                                 break;
         case ARMORY_DB_SUPER:                                break;
         default: 
            LOGERR << "Invalid DB mode in serializeStoredTxOutValue";
      }
   }

   uint16_t isCbase = (isCoinbase_ ? 1 : 0);

   BitPacker<uint16_t> bitpack;
   bitpack.putBits((uint16_t)ARMORY_DB_VERSION,  4);
   bitpack.putBits((uint16_t)txVersion_,         2);
   bitpack.putBits((uint16_t)writeSpent,         2);
   bitpack.putBit(           isCoinbase_);

   bw.put_BitPacker(bitpack);
   bw.put_BinaryData(dataCopy_);  // 8-byte value, var_int sz, pkscript
   
   if(writeSpent == TXOUT_SPENT)
   {
      if(spentByTxInKey_.getSize()==0)
         LOGERR << "Need to write out spentByTxIn but no spentness data";
      bw.put_BinaryData(spentByTxInKey_);
   }

}



////////////////////////////////////////////////////////////////////////////////
Tx StoredTx::getTxCopy(void) const
{
   if(!haveAllTxOut())
   {
      LOGERR << "Cannot get tx copy, because don't have full StoredTx!";
      return Tx();
   }

   return Tx(getSerializedTx());
}


////////////////////////////////////////////////////////////////////////////////
StoredTx & StoredTx::createFromTx(Tx & tx, bool doFrag, bool withTxOuts)
{
   if(!tx.isInitialized())
   {
      LOGERR << "Creating storedtx from uninitialized tx. Aborting.";
      isInitialized_ = false;
      return *this;
   }

   thisHash_  = tx.getThisHash();
   numTxOut_  = tx.getNumTxOut();
   version_   = tx.getVersion();
   lockTime_  = tx.getLockTime(); 
   numBytes_  = tx.getSize(); 
   isFragged_ = doFrag;

   uint32_t span = tx.getTxOutOffset(numTxOut_) - tx.getTxOutOffset(0);
   fragBytes_ = numBytes_ - span;

   if(!doFrag)
   {
      dataCopy_ = tx.serialize(); 
      isInitialized_ = true;
   }
   else
   {
      BinaryRefReader brr(tx.getPtr(), tx.getSize());
      uint32_t firstOut  = tx.getTxOutOffset(0);
      uint32_t afterLast = tx.getTxOutOffset(numTxOut_);
      uint32_t span = afterLast - firstOut;
      dataCopy_.resize(tx.getSize() - span);
      brr.get_BinaryData(dataCopy_.getPtr(), firstOut);
      brr.advance(span);
      brr.get_BinaryData(dataCopy_.getPtr()+firstOut, 4);
      isInitialized_ = true;
   }

   if(withTxOuts)
   {
      for(uint32_t txo = 0; txo < tx.getNumTxOut(); txo++)
      {
         stxoMap_[txo] = StoredTxOut();
         StoredTxOut & stxo = stxoMap_[txo];

         stxo.unserialize(tx.getTxOut(txo).serialize());
         stxo.txVersion_      = tx.getVersion();
         stxo.txIndex_        = tx.getBlockTxIndex();
         stxo.txOutIndex_     = txo;
         stxo.isCoinbase_     = tx.getTxIn(0).isCoinbase();
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

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxOut::getSerializedTxOut(void) const
{
   if(!isInitialized())
   {
      LOGERR << "Attempted to get serialized TxOut, but not initialized";
      return BinaryData(0);
   }
   return dataCopy_;
}

////////////////////////////////////////////////////////////////////////////////
TxOut StoredTxOut::getTxOutCopy(void) const
{
   if(!isInitialized())
   {
      LOGERR << "Attempted to get TxOut copy but not initialized";
      return TxOut();
   }
   return TxOut(dataCopy_.getPtr());
}



////////////////////////////////////////////////////////////////////////////////
// The list of spent/unspent txOuts is exactly what is needed to construct 
// a full vector<TxIOPair> for each address.  Keep in mind that this list
// only contains TxOuts and spentness of those TxOuts that are:
//    (1) Already in the blockchain
//    (2) On the longest chain at the time is was written
// It contains no zero-confirmation tx data, and it may not be accurate 
// if there was a reorg since it was written.  Part of the challenge of 
// implementing this DB stuff correctly is making sure both conditions 
// above are adhered to, despite TxIOPair objects being used in RAM to store
// zero-confirmation data as well as in-blockchain data.
void StoredScriptHistory::unserializeDBValue(BinaryRefReader & brr)
{
   // Now read the stored data fro this registered address
   BitUnpacker<uint16_t> bitunpack(brr);
   version_                     =                    bitunpack.getBits(4);
   DB_PRUNE_TYPE pruneType      = (DB_PRUNE_TYPE)    bitunpack.getBits(2);
   SCRIPT_UTXO_TYPE txoListType = (SCRIPT_UTXO_TYPE) bitunpack.getBits(2);
   hasMultisigEntries_          =                    bitunpack.getBit();

   alreadyScannedUpToBlk_ = brr.get_uint32_t();

   if(txoListType == SCRIPT_UTXO_TREE)
   {
      // This is where we might implement the Reiner-Tree concept, by
      // having only a reference to one TxOut here, but it's actually 
      // the root of some kind of authenticated tree structure.
      LOGERR << "TXO-trees are not implemented, yet!";
      return;
   }
   else if(txoListType == SCRIPT_UTXO_VECTOR)
   {
      // Get the TxOut list if a pointer was supplied
      // This list is unspent-TxOuts only if pruning enabled.  You will
      // have to dereference each one to check spentness if not pruning
      uint32_t numTxo = (uint32_t)(brr.get_var_int());
      txioVect_.reserve(numTxo);
      for(uint32_t i=0; i<numTxo; i++)
      {
         BitUnpacker<uint8_t> bitunpack(brr);
         bool isFromSelf  = bitunpack.getBit();
         bool isCoinbase  = bitunpack.getBit();
         bool isSpent     = bitunpack.getBit();

         // We always include the value, here
         uint64_t txoValue  = brr.get_uint64_t();

         TxIOPair txio;
         if(!isSpent)
         {
            BinaryDataRef  txokey = brr.get_BinaryDataRef(6);
            uint16_t       txoidx = brr.get_uint16_t();

            txio = TxIOPair(TxRef(txokey), txoidx);
         }
         else
         {
            BinaryDataRef  txokey = brr.get_BinaryDataRef(6);
            uint16_t       txoidx = brr.get_uint16_t();
            BinaryDataRef  txikey = brr.get_BinaryDataRef(6);
            uint16_t       txiidx = brr.get_uint16_t();

            txio = TxIOPair(TxRef(txokey), txoidx, 
                            TxRef(txikey), txiidx);

         }
         txio.setValue(txoValue);
         txio.setTxOutFromSelf(isFromSelf);
         txio.setFromCoinbase(isCoinbase);
         txioVect_.push_back(txio);
      }
   }

}

void StoredScriptHistory::serializeDBValue(BinaryWriter & bw ) const
{
   // Write out all the flags
   BitPacker<uint16_t> bitpack;
   bitpack.putBits((uint16_t)ARMORY_DB_VERSION,       4);
   bitpack.putBits((uint16_t)ARMDB.getDbPruneType(),  2);
   bitpack.putBits((uint16_t)SCRIPT_UTXO_VECTOR,      2);
   bitpack.putBit(hasMultisigEntries_);
   bw.put_BitPacker(bitpack);

   // 
   bw.put_uint32_t(alreadyScannedUpToBlk_); 

   if(UTXO_STORAGE == SCRIPT_UTXO_TREE)
   {
      // This is where we might implement the Reiner-Tree concept, by
      // having only a reference to one TxOut here, but it's actually 
      // the root of some kind of authenticated tree structure.
      LOGERR << "TXO-trees are not implemented, yet!";
      return;
   }
   else if(UTXO_STORAGE == SCRIPT_UTXO_VECTOR)
   {
      // Get the TxOut list if a pointer was supplied
      // This list is unspent-TxOuts only if pruning enabled.  You will
      // have to dereference each one to check spentness if not pruning
      uint32_t numTxo = (uint32_t)txioVect_.size();
      for(uint32_t i=0; i<numTxo; i++)
      {
         TxIOPair const & txio = txioVect_[i];
         bool isSpent = txio.hasTxInInMain();

         // If spent and only maintaining a pruned DB, skip it
         if(isSpent && ARMDB.getDbPruneType()==DB_PRUNE_ALL)
            continue;

         BitPacker<uint8_t> bitpack;
         bitpack.putBit(txio.isTxOutFromSelf());
         bitpack.putBit(txio.isFromCoinbase());
         bitpack.putBit(txio.hasTxInInMain());
         bw.put_BitPacker(bitpack);

         // Always write the value and 8-byte TxOut
         bw.put_uint64_t(txio.getValue());
         bw.put_BinaryData(txio.getTxRefOfOutput().getDBKeyRef());
         bw.put_uint16_t(txio.getIndexOfOutput());

         // If not supposed to write the TxIn, we would've bailed earlier
         if(isSpent)
         {
            if(!txio.getTxRefOfInput().isInitialized())
               bw.put_uint64_t(0);  // write 0x00*8 for "UNKNOWN"
            else
            {
               bw.put_BinaryData(txio.getTxRefOfInput().getDBKeyRef());
               bw.put_uint16_t(txio.getIndexOfInput());
            }
         }
      }
   }

}



////////////////////////////////////////////////////////////////////////////////
string DBUtils::getPrefixName(uint8_t prefixInt)
{
   return getPrefixName((DB_PREFIX)prefixInt);
}

////////////////////////////////////////////////////////////////////////////////
string DBUtils::getPrefixName(DB_PREFIX pref)
{
   switch(pref)
   {
      case DB_PREFIX_DBINFO:    return string("DBINFO"); 
      case DB_PREFIX_TXDATA:   return string("BLKDATA"); 
      case DB_PREFIX_SCRIPT:    return string("SCRIPT"); 
      case DB_PREFIX_TXHINTS:   return string("TXHINTS"); 
      case DB_PREFIX_TRIENODES: return string("TRIENODES"); 
      case DB_PREFIX_HEADHASH:  return string("HEADHASH"); 
      case DB_PREFIX_HEADHGT:   return string("HEADHGT"); 
      case DB_PREFIX_UNDODATA:  return string("UNDODATA"); 
      default:                  return string("<unknown>"); 
   }
}

/////////////////////////////////////////////////////////////////////////////
bool DBUtils::checkPrefixByte( BinaryRefReader brr, 
                               DB_PREFIX prefix,
                               bool rewindWhenDone)
{
   uint8_t oneByte = brr.get_uint8_t();
   bool out;
   if(oneByte == (uint8_t)prefix)
      out = true;
   else
   {
      LOGERR << "Unexpected prefix byte: "
                 << "Expected: " << getPrefixName(prefix)
                 << "Received: " << getPrefixName(oneByte);
      out = false;
   }

   if(rewindWhenDone)
      brr.rewind(1);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey( uint32_t height, 
                                   uint8_t  dup)
{
   BinaryWriter bw(5);
   bw.put_uint8_t(    DB_PREFIX_TXDATA );
   bw.put_BinaryData( heightAndDupToHgtx(height,dup) );
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey( uint32_t height, 
                                   uint8_t  dup,
                                   uint16_t txIdx)
{
   BinaryWriter bw(7);
   bw.put_uint8_t(    DB_PREFIX_TXDATA );
   bw.put_BinaryData( heightAndDupToHgtx(height,dup) );
   bw.put_uint16_t(   txIdx );
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKey( uint32_t height, 
                                   uint8_t  dup,
                                   uint16_t txIdx,
                                   uint16_t txOutIdx)
{
   BinaryWriter bw(9);
   bw.put_uint8_t(    DB_PREFIX_TXDATA );
   bw.put_BinaryData( heightAndDupToHgtx(height,dup) );
   bw.put_uint16_t(   txIdx );
   bw.put_uint16_t(   txOutIdx );
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix( uint32_t height, 
                                           uint8_t  dup)
{
   return heightAndDupToHgtx(height,dup);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix( uint32_t height, 
                                           uint8_t  dup,
                                           uint16_t txIdx)
{
   BinaryWriter bw(6);
   bw.put_BinaryData( heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(   txIdx);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::getBlkDataKeyNoPrefix( uint32_t height, 
                                           uint8_t  dup,
                                           uint16_t txIdx,
                                           uint16_t txOutIdx)
{
   BinaryWriter bw(8);
   bw.put_BinaryData( heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(   txIdx);
   bw.put_uint16_t(   txOutIdx);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
uint32_t DBUtils::hgtxToHeight(BinaryData hgtx)
{
   return (READ_UINT32_LE(hgtx) >> 8);

}

/////////////////////////////////////////////////////////////////////////////
uint8_t DBUtils::hgtxToDupID(BinaryData hgtx)
{
   return (READ_UINT32_LE(hgtx) & 0x7f);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBUtils::heightAndDupToHgtx(uint32_t hgt, uint8_t dup)
{
   uint32_t hgtxInt = (hgt<<8) | (uint32_t)dup;
   return WRITE_UINT32_LE(hgtxInt);
}
