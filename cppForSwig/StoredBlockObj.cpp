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

#include <vector>
#include <list>
#include <map>
#include "StoredBlockObj.h"
#include "DbHeader.h"

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredDBInfo::getDBKey(uint16_t id)
{
   BinaryWriter bw(3);
   bw.put_uint8_t((uint8_t)DB_PREFIX_DBINFO);
   bw.put_uint16_t(id, BE);

   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
void StoredDBInfo::unserializeDBValue(BinaryRefReader & brr)
{
   if(brr.getSizeRemaining() < 44)
   {
      magic_.resize(0);
      topBlkHgt_ = UINT32_MAX;
      metaHash_.resize(0);
      return;
   }
   brr.get_BinaryData(magic_, 4);
   
   BitUnpacker<uint32_t> bitunpack(brr);
   armoryVer_  =                 bitunpack.getBits(16);
   if (armoryVer_ != ARMORY_DB_VERSION)
   {
      stringstream ss;
      ss << "DB version mismatch. Use another dbdir or empty the current one!";
      LOGERR << ss.str();
      throw DbErrorMsg(ss.str());
   }

   armoryType_ = (ARMORY_DB_TYPE)bitunpack.getBits(4);
   
   topBlkHgt_    = brr.get_uint32_t();
   appliedToHgt_ = brr.get_uint32_t();
   brr.get_BinaryData(metaHash_, 32);

   if (brr.getSizeRemaining() == 32)
      brr.get_BinaryData(topScannedBlkHash_, 32);
}

/////////////////////////////////////////////////////////////////////////////
void StoredDBInfo::serializeDBValue(BinaryWriter & bw ) const
{
   BitPacker<uint32_t> bitpack;
   bitpack.putBits((uint32_t)armoryVer_,   16);
   bitpack.putBits((uint32_t)armoryType_,  4);

   bw.put_BinaryData(magic_);
   bw.put_BitPacker(bitpack);
   bw.put_uint32_t(topBlkHgt_); // top blk height
   bw.put_uint32_t(appliedToHgt_); // top blk height
   
   if (metaHash_.getSize() == 0)
      bw.put_BinaryData(BtcUtils::EmptyHash());
   else
      bw.put_BinaryData(metaHash_);

   if (topScannedBlkHash_.getSize())
      bw.put_BinaryData(topScannedBlkHash_);
}

////////////////////////////////////////////////////////////////////////////////
void StoredDBInfo::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredDBInfo::unserializeDBValue(BinaryDataRef bdr)
                                  
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}

/////////////////////////////////////////////////////////////////////////////
void StoredDBInfo::pprintOneLine(uint32_t indent)
{
   for(uint32_t i=0; i<indent; i++)
      cout << " ";
   
   cout << "DBINFO: " 
        << " TopBlk: " << topBlkHgt_
        << " , " << metaHash_.getSliceCopy(0,4).toHexStr().c_str()
        << endl;
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::setKeyData(uint32_t hgt, uint8_t dupID)
{
   // Set the params for this SBH object
   blockHeight_  = hgt;
   duplicateID_  = dupID;

   // Then trickle down to each StoredTx object (if any)
   map<uint16_t, StoredTx>::iterator iter;     
   for(iter = stxMap_.begin(); iter != stxMap_.end(); iter++)
      iter->second.setKeyData(hgt, dupID, iter->first);
}

/////////////////////////////////////////////////////////////////////////////
void DBBlock::setHeightAndDup(uint32_t hgt, uint8_t dupID)
{
   blockHeight_ = hgt;
   duplicateID_ = dupID;
}

/////////////////////////////////////////////////////////////////////////////
void DBBlock::setHeightAndDup(BinaryData hgtx)
{
   blockHeight_ = DBUtils::hgtxToHeight(hgtx);
   duplicateID_ = DBUtils::hgtxToDupID(hgtx);
}

/////////////////////////////////////////////////////////////////////////////
bool StoredHeader::haveFullBlock(void) const
{
   if(dataCopy_.getSize() != HEADER_SIZE)
      return false;

   for(uint16_t tx=0; tx<numTx_; tx++)
   {
      map<uint16_t, StoredTx>::const_iterator iter = stxMap_.find(tx);
      if(ITER_NOT_IN_MAP(iter, stxMap_))
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
BinaryData DBBlock::getDBKey(bool withPrefix) const
{
   if(blockHeight_==UINT32_MAX || duplicateID_==UINT8_MAX)
   {
      throw std::range_error("Requesting DB key for incomplete SBH");
   }

   if(withPrefix)
      return DBUtils::getBlkDataKey(blockHeight_, duplicateID_);
   else
      return DBUtils::getBlkDataKeyNoPrefix(blockHeight_, duplicateID_);

}



/////////////////////////////////////////////////////////////////////////////
void DBBlock::createFromBlockHeader(const BlockHeader & bh)
{
   if(!bh.isInitialized())
   {
      LOGERR << "trying to create from uninitialized block header";
      return;
   } 

   setHeaderData(bh.serialize());

   numTx_ = bh.getNumTx();
   numBytes_ = bh.getBlockSize();
   blockHeight_ = bh.getBlockHeight();
   duplicateID_ = UINT8_MAX;
   isMainBranch_ = bh.isMainBranch();
   hasBlockHeader_ = true;

   fileID_ = bh.getBlockFileNum();
   offset_ = bh.getOffset();

   uniqueID_ = bh.getThisID();
}

////////////////////////////////////////////////////////////////////////////////
Tx StoredHeader::getTxCopy(uint16_t i)
{ 
   if(KEY_IN_MAP(i, stxMap_))
      return stxMap_[i].getTxCopy();
   else
      return Tx();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredHeader::getSerializedTx(uint16_t i)
{ 
   if(KEY_IN_MAP(i, stxMap_))
      return stxMap_[i].getSerializedTx();
   else
      return BinaryData(0);
}

/////////////////////////////////////////////////////////////////////////////
void DBBlock::setHeaderData(BinaryData const & header80B)
{
   if(header80B.getSize() != HEADER_SIZE)
   {
      LOGERR << "Asked to unserialize a non-80-byte header";
      return;
   }
   dataCopy_.copyFrom(header80B);
   BtcUtils::getHash256(header80B, thisHash_);
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::unserializeSimple(BinaryRefReader brr)
{
   uint32_t height = blockHeight_;
   uint8_t  dupid = duplicateID_;

   vector<BinaryData> allTxHashes;
   BlockHeader bh(brr);
   uint32_t nTx = (uint32_t)brr.get_var_int();

   createFromBlockHeader(bh);
   numTx_ = nTx;

   blockHeight_ = height;
   duplicateID_ = dupid;

   numBytes_ = HEADER_SIZE + BtcUtils::calcVarIntSize(numTx_);
   if (dataCopy_.getSize() != HEADER_SIZE)
   {
      LOGERR << "Unserializing header did not produce 80-byte object!";
      return;
   }

   if (numBytes_ > brr.getSize())
   {
      LOGERR << "Anticipated size of block header is more than what we have";
      throw BlockDeserializingException();
   }

   BtcUtils::getHash256(dataCopy_, thisHash_);

   for (uint32_t tx = 0; tx < nTx; tx++)
   {
      // gather tx hashes
      Tx thisTx(brr);

      StoredTx stx;
      stx.thisHash_ = thisTx.getThisHash();
      stxMap_[tx] = move(stx);
   }
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::unserializeFullBlock(BinaryRefReader brr, 
                                        bool doFrag,
                                        bool withPrefix)
{
   if(withPrefix)
   {
      BinaryData magic  = brr.get_BinaryData(4);
      uint32_t   nBytes = brr.get_uint32_t();

      if(brr.getSizeRemaining() < nBytes)
      {
         LOGERR << "Not enough bytes remaining in BRR to read block";
         return;
      }
   }

   uint32_t height = blockHeight_;
   uint8_t  dupid  = duplicateID_;

   vector<BinaryData> allTxHashes;
   BlockHeader bh(brr); 
   uint32_t nTx = (uint32_t)brr.get_var_int();

   createFromBlockHeader(bh);
   numTx_ = nTx;
   
   blockHeight_ = height;
   duplicateID_ = dupid;

   numBytes_ = HEADER_SIZE + BtcUtils::calcVarIntSize(numTx_);
   if(dataCopy_.getSize() != HEADER_SIZE)
   {
      LOGERR << "Unserializing header did not produce 80-byte object!";
      return;
   }
   
   if (numBytes_ > brr.getSize())
   {
      LOGERR << "Anticipated size of block header is more than what we have";
      throw BlockDeserializingException();
   }

   BtcUtils::getHash256(dataCopy_, thisHash_);

   for(uint32_t tx=0; tx<nTx; tx++)
   {
      // We're going to have to come back to the beginning of the tx, later
      uint32_t txStart = brr.getPosition();

      // Read a regular tx and then convert it
      Tx thisTx(brr);
      numBytes_ += thisTx.getSize();

      //save the hash for merkle computation
      allTxHashes.push_back(thisTx.getThisHash());

      // Now add it to the map
      stxMap_[tx] = StoredTx();
      StoredTx & stx = stxMap_[tx];

      // Now copy the appropriate data from the vanilla Tx object
      stx.createFromTx(thisTx, doFrag, true);
      stx.isFragged_     = doFrag;
      stx.version_       = thisTx.getVersion();
      stx.txIndex_       = tx;

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
         stxo.duplicateID_    = UINT8_MAX;
         stxo.txIndex_        = tx;
         stxo.txOutIndex_     = txo;
         stxo.isCoinbase_     = thisTx.getTxInCopy(0).isCoinbase();
         stxo.parentHash_     = stx.thisHash_;
      }

      // Sitting at the nLockTime, 4 bytes before the end
      brr.advance(4);

      // Finally, add the 
      stxMap_[tx] = stx;
   }

   if (nTx == 0 || nTx != allTxHashes.size())
   {
	   LOGERR << "Mismatch between numtx and allTxHashes.size() or 0 tx in block";
	   throw BlockDeserializingException();
   }

   //compute the merkle root and compare to the header's
   BinaryData computedMerkleRoot = BtcUtils::calculateMerkleRoot(allTxHashes);

   if (computedMerkleRoot != bh.getMerkleRoot())
   {
      LOGERR << "Merkle root mismatch! Raw block data is corrupt!";
      throw BlockDeserializingException();
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
BlockHeader DBBlock::getBlockHeaderCopy(void) const
{
   if(!isInitialized())
      return BlockHeader(); 

   BlockHeader bh(dataCopy_);

   bh.setNumTx(numTx_);
   bh.setBlockSize(numBytes_);
   bh.setDuplicateID(duplicateID_);

   bh.setBlockFileNum(fileID_);
   bh.setBlockFileOffset(offset_);

   return bh;
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBBlock::getSerializedBlockHeader(void) const
{
   if(!isInitialized())
      return BinaryData(0);

   return dataCopy_;
}

////////////////////////////////////////////////////////////////////////////////
void DBBlock::unserializeDBValue(DB_SELECT db,
                                      BinaryData const & bd,
                                      bool ignoreMerkle)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(db, brr, ignoreMerkle);
}

////////////////////////////////////////////////////////////////////////////////
void DBBlock::unserializeDBValue(DB_SELECT db,
                                      BinaryDataRef bdr,
                                      bool ignoreMerkle)
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(db, brr, ignoreMerkle);
}

/////////////////////////////////////////////////////////////////////////////
void DBBlock::unserializeDBValue( DB_SELECT         db,
                                       BinaryRefReader & brr,
                                       bool              ignoreMerkle)
{

   if(db==HEADERS)
   {
      if(brr.getSize() < HEADER_SIZE + 26)
      {
         stringstream err;
         err << "buffer is too small: " << dataCopy_.getSize();
         err << " bytes. expected: " << HEADER_SIZE + 26;

         LOGERR << err.str();
         throw BlockDeserializingException(err.str());
      }

      brr.get_BinaryData(dataCopy_, HEADER_SIZE);
      BinaryData hgtx = brr.get_BinaryData(4);
      blockHeight_ = DBUtils::hgtxToHeight(hgtx);
      duplicateID_ = DBUtils::hgtxToDupID(hgtx);
      BtcUtils::getHash256(dataCopy_, thisHash_);
      numBytes_ = brr.get_uint32_t();
      numTx_ = brr.get_uint32_t();
      fileID_ = brr.get_uint16_t();
      offset_ = brr.get_uint64_t();
      uniqueID_ = brr.get_uint32_t();
   }
   else if(db==BLKDATA)
   {
      if(brr.getSize() < HEADER_SIZE + 12)
      {
         stringstream err;
         err << "buffer is too small: " << dataCopy_.getSize();
         err << " bytes. expected: " << HEADER_SIZE + 12;

         LOGERR << err.str();
         throw BlockDeserializingException(err.str());
      }

      // Read the flags byte
      BitUnpacker<uint32_t> bitunpack(brr);
      unserArmVer_      =                  bitunpack.getBits(16);
      unserBlkVer_      =                  bitunpack.getBits(4);
      unserDbType_      = (ARMORY_DB_TYPE) bitunpack.getBits(4);
      unserMkType_      = (MERKLE_SER_TYPE)bitunpack.getBits(2);
      blockAppliedToDB_ =                  bitunpack.getBit();
   
      // Unserialize the raw header into the SBH object
      brr.get_BinaryData(dataCopy_, HEADER_SIZE);
      BtcUtils::getHash256(dataCopy_, thisHash_);
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
void DBBlock::serializeDBValue(
   BinaryWriter &  bw,
   DB_SELECT       db,
   ARMORY_DB_TYPE dbType
) const
{
   if(!isInitialized())
   {
      LOGERR << "Attempted to serialize uninitialized block header";
      return;
   }

   if(db==HEADERS)
   {
      BinaryData hgtx = DBUtils::heightAndDupToHgtx(blockHeight_, duplicateID_);
      bw.put_BinaryData(dataCopy_);
      bw.put_BinaryData(hgtx);
      bw.put_uint32_t(numBytes_);
      bw.put_uint32_t(numTx_);
      bw.put_uint16_t(fileID_);
      bw.put_uint64_t(offset_);
      bw.put_uint32_t(uniqueID_);
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
      switch(dbType)
      {
         // If we store all the tx anyway, don't need any/partial merkle trees
         case ARMORY_DB_BARE:    mtype = MERKLE_SER_NONE;    break;
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
      bitpack.putBits((uint32_t)ARMORY_DB_VERSION,         16);
      bitpack.putBits((uint32_t)version,                   4);
      bitpack.putBits((uint32_t)dbType,                    4);
      bitpack.putBits((uint32_t)mtype,                     2);
      bitpack.putBit(blockAppliedToDB_);

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
void DBBlock::unserializeDBKey(DB_SELECT db, BinaryDataRef key)
{
   if(db==BLKDATA)
   {
      BinaryRefReader brr(key);
      if(key.getSize() == 4)
         DBUtils::readBlkDataKeyNoPrefix(brr, blockHeight_, duplicateID_);
      else if(key.getSize() == 5)
         DBUtils::readBlkDataKey(brr, blockHeight_, duplicateID_);
      else
         LOGERR << "Invalid key for StoredHeader";
   }
   else
      LOGERR << "This method not intended for HEADERS DB";
}


/////////////////////////////////////////////////////////////////////////////
void DBBlock::pprintOneLine(uint32_t indent)
{
   for(uint32_t i=0; i<indent; i++)
      cout << " ";
   
   cout << "HEADER: " << thisHash_.getSliceCopy(0,4).toHexStr()
        << " (" << blockHeight_ << "," << (uint32_t)duplicateID_ << ")"
        << "     #Tx: " << numTx_
        << " Applied: " << (blockAppliedToDB_ ? "T" : "F")
        << endl;
}

/////////////////////////////////////////////////////////////////////////////
void StoredHeader::pprintFullBlock(uint32_t indent)
{
   pprintOneLine(indent);
   if(numTx_ > 10000)
   {
      cout << "      <No tx to print>" << endl;
      return;
   }

   for(uint32_t i=0; i<numTx_; i++)
      stxMap_[i].pprintFullTx(indent+3);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBTx::getDBKey(bool withPrefix) const
{
   if(blockHeight_ == UINT32_MAX || 
      duplicateID_ == UINT8_MAX  || 
      txIndex_     == UINT16_MAX)
   {
      LOGERR << "Requesting DB key for incomplete STX";
      return BinaryData(0);
   }

   if(withPrefix)
      return DBUtils::getBlkDataKey(blockHeight_, duplicateID_, txIndex_);
   else
      return DBUtils::getBlkDataKeyNoPrefix(blockHeight_, duplicateID_, txIndex_);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData DBTx::getDBKeyOfChild(uint16_t i, bool withPrefix) const
{
   return (getDBKey(withPrefix) + WRITE_UINT16_BE(i));
}

/////////////////////////////////////////////////////////////////////////////
void DBTx::unserialize(BinaryData const & data, bool fragged)
{
   BinaryRefReader brr(data);
   unserialize(brr, fragged);
}

/////////////////////////////////////////////////////////////////////////////
void DBTx::unserialize(BinaryDataRef data, bool fragged)
{
   BinaryRefReader brr(data);
   unserialize(brr, fragged);
}


/////////////////////////////////////////////////////////////////////////////
void DBTx::unserialize(BinaryRefReader & brr, bool fragged)
{
   vector<size_t> offsetsIn, offsetsOut; 
   uint32_t nbytes = BtcUtils::StoredTxCalcLength(brr.getCurrPtr(),
      brr.getSize(), fragged, &offsetsIn, &offsetsOut, nullptr);

   if (offsetsOut.size() < 1)
   {
      LOGERR << "Couldn't deserialize db value";
      return;
   }

   if(brr.getSizeRemaining() < nbytes)
   {
      LOGERR << "Not enough bytes in BRR to unserialize StoredTx";
      return;
   }

   brr.get_BinaryData(dataCopy_, nbytes);

   isFragged_ = fragged;
   numTxOut_  = offsetsOut.size()-1;
   txInCutOff_ = offsetsOut[0];

   version_   = READ_UINT32_LE(dataCopy_.getPtr());
   lockTime_  = READ_UINT32_LE(dataCopy_.getPtr() + nbytes - 4);
  

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
      BtcUtils::getHash256(dataCopy_, thisHash_);
   }
}


////////////////////////////////////////////////////////////////////////////////
void DBTx::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void DBTx::unserializeDBValue(BinaryDataRef bdr)
                                  
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}


/////////////////////////////////////////////////////////////////////////////
void DBTx::unserializeDBValue(BinaryRefReader & brr)
{
   // flags
   //    DBVersion      4 bits
   //    TxVersion      2 bits
   //    HowTxSer       4 bits   (FullTxOut, TxNoTxOuts, numTxOutOnly)
   BitUnpacker<uint32_t> bitunpack(brr); // flags
   unserArmVer_  =                    bitunpack.getBits(16);
   unserTxVer_   =                    bitunpack.getBits(2);
   unserTxType_  = (TX_SERIALIZE_TYPE)bitunpack.getBits(4);

   if(unserArmVer_ != ARMORY_DB_VERSION)
      LOGWARN << "Version mismatch in unserialize DB tx";
   
   brr.get_BinaryData(thisHash_, 32);

   if(unserTxType_ == TX_SER_FULL || unserTxType_ == TX_SER_FRAGGED)
      unserialize(brr, unserTxType_==TX_SER_FRAGGED);
   else
      numTxOut_ = (uint32_t)brr.get_var_int();

   if (brr.getSizeRemaining() == 4)
   {
      //this is for ZC tx, as regular Tx don't have custom time stamps
      unixTime_ = brr.get_uint32_t();
   }
}


/////////////////////////////////////////////////////////////////////////////
void StoredTx::serializeDBValue(
      BinaryWriter &    bw,
      ARMORY_DB_TYPE dbType
   ) const
{
   TX_SERIALIZE_TYPE serType;
   
   switch(dbType)
   {
      // In most cases, if storing separate TxOuts, fragged Tx is fine
      // UPDATE:  I'm not sure there's a good reason to NOT frag ever
      case ARMORY_DB_BARE:    serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_FULL:    serType = TX_SER_FRAGGED; break;
      case ARMORY_DB_SUPER:   serType = TX_SER_FRAGGED; break;
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

   BitPacker<uint32_t> bitpack;
   bitpack.putBits((uint32_t)ARMORY_DB_VERSION,  16);
   bitpack.putBits((uint32_t)version,            2);
   bitpack.putBits((uint32_t)serType,            4);

   
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
   if(!isInitialized())
      return false; 

   if(!isFragged_)
      return true;

   return stxoMap_.size()==numTxOut_;

}


////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTx::getSerializedTx(void) const
{
   if(!isInitialized())
      return BinaryData(0); 

   if(!isFragged_)
      return dataCopy_;
   else if(!haveAllTxOut())
      return BinaryData(0); 

   BinaryWriter bw;    
   if(numBytes_ != UINT32_MAX)
      bw.reserve(numBytes_);

   if (txInCutOff_ == SIZE_MAX)
      return BinaryData(0);

   bw.put_BinaryData(dataCopy_.getPtr(), txInCutOff_);

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

   bw.put_BinaryData(dataCopy_.getPtr()+txInCutOff_, 
      dataCopy_.getSize() - txInCutOff_);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData DBTx::getSerializedTxFragged(void) const
{
   if(!isInitialized())
      return BinaryData(0); 

   if(isFragged_)
      return dataCopy_;

   if(numBytes_ == UINT32_MAX)
   {
      LOGERR << "Do not know size of tx in order to serialize it";
      return BinaryData(0);
   }

   BinaryWriter bw;
   vector<size_t> outOffsets;
   BtcUtils::StoredTxCalcLength(dataCopy_.getPtr(), dataCopy_.getSize(),
      false, nullptr, &outOffsets, nullptr);
   uint32_t firstOut  = outOffsets[0];
   uint32_t afterLast = outOffsets[outOffsets.size()-1];
   uint32_t span = afterLast - firstOut;

   BinaryData output(dataCopy_.getSize() - span);
   dataCopy_.getSliceRef(0,  firstOut).copyTo(output.getPtr());
   dataCopy_.getSliceRef(afterLast, 4).copyTo(output.getPtr()+firstOut);
   return output;
}

/////////////////////////////////////////////////////////////////////////////
void DBTx::unserializeDBKey(BinaryDataRef key)
{
   BinaryRefReader brr(key);
   if(key.getSize() == 6)
      DBUtils::readBlkDataKeyNoPrefix(brr, blockHeight_, duplicateID_, txIndex_);
   else if(key.getSize() == 7)
      DBUtils::readBlkDataKey(brr, blockHeight_, duplicateID_, txIndex_);
   else
      LOGERR << "Invalid key for StoredTx";
}

////////////////////////////////////////////////////////////////////////////////
void DBTx::pprintOneLine(uint32_t indent)
{
   for(uint32_t i=0; i<indent; i++)
      cout << " ";
   
   cout << "TX:  " << thisHash_.getSliceCopy(0,4).toHexStr()
        << " (" << blockHeight_ 
        << "," << (uint32_t)duplicateID_ 
        << "," << txIndex_ << ")"
        << "   #TXO: " << numTxOut_
        << endl;
}

////////////////////////////////////////////////////////////////////////////////
void StoredTx::pprintFullTx(uint32_t indent)
{
   pprintOneLine(indent);
   if(numTxOut_ > 10000)
   {
      cout << "         <No txout to print>" << endl;
      return;
   }

   for(uint32_t i=0; i<numTxOut_; i++)
      stxoMap_[i].pprintOneLine(indent+3);
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

   uint32_t numBytes = BtcUtils::TxOutCalcLength(
      brr.getCurrPtr(), brr.getSizeRemaining());

   if(brr.getSizeRemaining() < numBytes)
   {
      LOGERR << "Not enough bytes in BRR to unserialize StoredTxOut";
      return;
   }

   brr.get_BinaryData(dataCopy_, numBytes);
}


////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserializeDBValue(BinaryDataRef bdr)
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
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
   isCoinbase_  =                  bitunpack.getBit();
   auto dbType  = (ARMORY_DB_TYPE) bitunpack.getBits(2);

   unserialize(brr);
   if(spentness_ == TXOUT_SPENT && brr.getSizeRemaining()>=8)
      spentByTxInKey_ = brr.get_BinaryData(8); 

   if (dbType != ARMORY_DB_SUPER)
      return;

   brr.get_BinaryData(parentHash_, 32);
   txOutIndex_ = brr.get_uint16_t();
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::serializeDBValue(BinaryWriter & bw, ARMORY_DB_TYPE dbType,
                                   bool forceSaveSpentness) const
{
   serializeDBValue(bw, dbType, forceSaveSpentness,
      txVersion_, isCoinbase_, spentness_, dataCopy_.getRef(),
      spentByTxInKey_.getRef(), parentHash_.getRef(), txOutIndex_);
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::serializeDBValue(
   BinaryWriter& bw,
   ARMORY_DB_TYPE dbType, bool forceSaveSpentness,
   uint16_t txVersion, bool isCoinbase,
   TXOUT_SPENTNESS spentness,
   const BinaryDataRef dataRef,
   const BinaryDataRef spentByTxIn,
   const BinaryDataRef hash,
   uint16_t txoutindex)
{
   TXOUT_SPENTNESS writeSpent = spentness;

   if (!forceSaveSpentness)
   {
      switch (dbType)
      {
         //// If the DB is in lite or partial modes, we don't bother recording
         //   spentness (in fact, if it's spent, this entry probably won't even
         //   be written to the DB).
      case ARMORY_DB_BARE:                                 break;
      case ARMORY_DB_FULL:                                 break;
      case ARMORY_DB_SUPER:                                break;
      default:
         LOGERR << "Invalid DB mode in serializeStoredTxOutValue";
      }
   }

   BitPacker<uint16_t> bitpack;
   bitpack.putBits((uint16_t)ARMORY_DB_VERSION, 4);
   bitpack.putBits((uint16_t)txVersion, 2);
   bitpack.putBits((uint16_t)writeSpent, 2);
   bitpack.putBit(isCoinbase);
   bitpack.putBits((uint16_t)dbType, 2);

   bw.put_BitPacker(bitpack);
   bw.put_BinaryData(dataRef);  // 8-byte value, var_int sz, pkscript

   if (writeSpent == TXOUT_SPENT)
   {
      if (spentByTxIn.getSize() == 0)
         LOGERR << "Need to write out spentByTxIn but no spentness data";
      bw.put_BinaryData(spentByTxIn);
   }

   if (dbType != ARMORY_DB_SUPER)
      return;

   bw.put_BinaryData(hash);
   bw.put_uint16_t(txoutindex);
}

/////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxOut::getDBKey(bool withPrefix) const
{
   if(blockHeight_ == UINT32_MAX || 
      duplicateID_ == UINT8_MAX  || 
      txIndex_     == UINT16_MAX ||
      txOutIndex_  == UINT16_MAX)
   {
      LOGERR << "Requesting DB key for incomplete STXO";
      LOGERR << "--- height: " << blockHeight_;
      LOGERR << "--- dupID: " << duplicateID_;
      LOGERR << "--- txIndex: " << txIndex_;
      LOGERR << "--- txOutIndex" << txOutIndex_;
      return BinaryData(0);
   }

   if(withPrefix)
      return DBUtils::getBlkDataKey(
                             blockHeight_, duplicateID_, txIndex_, txOutIndex_);
   else
      return DBUtils::getBlkDataKeyNoPrefix(
                             blockHeight_, duplicateID_, txIndex_, txOutIndex_);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxOut::getDBKeyOfParentTx(bool withPrefix) const
{
   BinaryData stxoKey = getDBKey(withPrefix);
   if(withPrefix)
      return stxoKey.getSliceCopy(0, 7);
   else
      return stxoKey.getSliceCopy(0, 6);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData& StoredTxOut::getHgtX(void)
{ 
   if (hgtX_.getSize())
      return hgtX_;

   hgtX_ = getDBKey(false).getSliceCopy(0, 4); 
   return hgtX_;
}

////////////////////////////////////////////////////////////////////////////////
bool StoredTxOut::matchesDBKey(BinaryDataRef dbkey) const
{
   if(dbkey.getSize() == 8)
      return (getDBKey(false) == dbkey);
   else if(dbkey.getSize() == 9)
      return (getDBKey(true) == dbkey);
   else
   {
      LOGERR << "Non STXO-DBKey passed in to check match against STXO";
      return false;
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
   
   Tx returnTx(getSerializedTx());
   if(blockHeight_ != UINT32_MAX)
      returnTx.setTxRef(TxRef(getDBKey(false)));
   returnTx.setRBF(isRBF_);
   return returnTx;
}

////////////////////////////////////////////////////////////////////////////////
void StoredTx::setKeyData(uint32_t height, uint8_t dup, uint16_t txIdx)
{
   blockHeight_ = height;
   duplicateID_ = dup;
   txIndex_     = txIdx;

   map<uint16_t, StoredTxOut>::iterator iter;
   for(iter  = stxoMap_.begin();  iter != stxoMap_.end(); iter++)
   {
      iter->second.blockHeight_ = height;
      iter->second.duplicateID_ = dup;
      iter->second.txIndex_     = txIdx;
      iter->second.txOutIndex_  = iter->first;
   }
}

////////////////////////////////////////////////////////////////////////////////
StoredTx & StoredTx::createFromTx(BinaryDataRef rawTx, bool doFrag, bool withTxOuts)
{
   Tx tx(rawTx);
   return createFromTx(tx, doFrag, withTxOuts);
}

////////////////////////////////////////////////////////////////////////////////
StoredTx & StoredTx::createFromTx(Tx & tx, bool doFrag, bool withTxOuts)
{
   if(!tx.isInitialized())
   {
      LOGERR << "Creating storedtx from uninitialized tx. Aborting.";
      dataCopy_.resize(0);
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
   txInCutOff_ = tx.getTxOutOffset(0);

   if(!doFrag)
      dataCopy_ = tx.serialize(); 
   else
   {
      BinaryRefReader brr(tx.getPtr(), tx.getSize());
      uint32_t firstOut  = tx.getTxOutOffset(0);
      uint32_t afterLast = tx.getTxOutOffset(numTxOut_);
      uint32_t _span = afterLast - firstOut;
      dataCopy_.resize(tx.getSize() - _span);
      brr.get_BinaryData(dataCopy_.getPtr(), firstOut);
      brr.advance(_span);
      brr.get_BinaryData(dataCopy_.getPtr()+firstOut, brr.getSizeRemaining());
   }

   if(withTxOuts)
   {
      for(uint32_t txo = 0; txo < tx.getNumTxOut(); txo++)
      {
         stxoMap_[txo] = StoredTxOut();
         StoredTxOut & stxo = stxoMap_[txo];

         stxo.unserialize(tx.getTxOutCopy(txo).serialize());
         stxo.txVersion_      = tx.getVersion();
         stxo.txIndex_        = tx.getBlockTxIndex();
         stxo.txOutIndex_     = txo;
         stxo.isCoinbase_     = tx.getTxInCopy(0).isCoinbase();
         stxo.parentHash_     = thisHash_;
      }
   }

   //only significant for ZC
   unixTime_ = tx.getTxTime();

   return *this;
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut & StoredTxOut::createFromTxOut(TxOut & txout)
{
   unserialize(txout.serialize());
   return *this;
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
   TxOut o;
   o.unserialize_checked(dataCopy_.getPtr(), dataCopy_.getSize());
   return o;
}

////////////////////////////////////////////////////////////////////////////////
const BinaryData& StoredTxOut::getScrAddress(void) const
{
   if (scrAddr_.getSize() > 0)
      return scrAddr_;

   BinaryRefReader brr(dataCopy_);
   brr.advance(8);
   uint32_t scrsz = (uint32_t)brr.get_var_int();
   scrAddr_ = BtcUtils::getTxOutScrAddr(brr.get_BinaryDataRef(scrsz));

   return scrAddr_;
}

////////////////////////////////////////////////////////////////////////////////
BinaryDataRef StoredTxOut::getScriptRef(void) const
{
   BinaryRefReader brr(dataCopy_);
   brr.advance(8);
   uint32_t scrsz = (uint32_t)brr.get_var_int();
   return brr.get_BinaryDataRef(scrsz);
}

////////////////////////////////////////////////////////////////////////////////
uint64_t StoredTxOut::getValue(void) const
{
   if(!isInitialized())
      return UINT64_MAX;

   return *(uint64_t*)dataCopy_.getPtr();
}

/////////////////////////////////////////////////////////////////////////////
void StoredTxOut::unserializeDBKey(BinaryDataRef key)
{
   BinaryRefReader brr(key);
   if(key.getSize() == 8)
      DBUtils::readBlkDataKeyNoPrefix(brr, blockHeight_, duplicateID_, txIndex_, txOutIndex_);
   else if(key.getSize() == 9)
      DBUtils::readBlkDataKey(brr, blockHeight_, duplicateID_, txIndex_, txOutIndex_);
   else
      LOGERR << "Invalid key for StoredTxOut";
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxOut::pprintOneLine(uint32_t indent)
{
   for(uint32_t i=0; i<indent; i++)
      cout << " ";

   string pprintHash("");
   if(parentHash_.getSize() > 0)
      pprintHash = parentHash_.getSliceCopy(0,4).toHexStr();
  
   cout << "TXOUT:   "
        << "  (" << blockHeight_ 
        << "," << (uint32_t)duplicateID_ 
        << "," << txIndex_
        << "," << txOutIndex_ << ")"
        << " Value=" << (double)(getValue())/(100000000.0)
        << " isCB: " << (isCoinbase_ ? "(X)" : "   ");

   if(spentness_ == TXOUT_SPENTUNK)
        cout << " Spnt: " << "<-----UNKNOWN---->" << endl;
   else if(spentness_ == TXOUT_UNSPENT)
        cout << " Spnt: " << "<                >" << endl;
   else 
        cout << " Spnt: " << "<" << spentByTxInKey_.toHexStr() << ">" << endl;
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
   auto dbType = (ARMORY_DB_TYPE)bitunpack.getBits(4);

   if (dbType != ARMORY_DB_SUPER)
   {
      scanHeight_ = brr.get_int32_t();
      tallyHeight_ = brr.get_int32_t();
   }

   totalTxioCount_ = brr.get_var_int();
   
   subHistMap_.clear();
   subsshSummary_.clear();

   // We shouldn't end up with empty ssh's, but should catch it just in case
   if(totalTxioCount_==0)
      return;
   
   try
   {
      totalUnspent_ = brr.get_uint64_t();

      //
      auto sumSize = brr.get_uint32_t();
      for (unsigned i = 0; i < sumSize; i++)
      {
         unsigned height = brr.get_var_int();
         unsigned sum = brr.get_var_int();

         subsshSummary_[height] = sum;
      }
   }
   catch (runtime_error& e)
   {
      LOGERR << "StoredScriptHistory deser error";
      throw e;
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::serializeDBValue(BinaryWriter & bw, 
   ARMORY_DB_TYPE dbType) 
   const
{
   // Write out all the flags
   BitPacker<uint16_t> bitpack;
   bitpack.putBits((uint16_t)dbType,                  4);
   bitpack.putBits((uint16_t)SCRIPT_UTXO_VECTOR,      2);
   bw.put_BitPacker(bitpack);

   //
   if (dbType != ARMORY_DB_SUPER)
   {
      bw.put_int32_t(scanHeight_);
      bw.put_int32_t(tallyHeight_);
   }
      
   bw.put_var_int(totalTxioCount_);
   bw.put_uint64_t(totalUnspent_);

   //
   bw.put_uint32_t(subsshSummary_.size());
   for (auto& sum : subsshSummary_)
   {
      bw.put_var_int(sum.first);
      bw.put_var_int(sum.second);
   }
}


////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::unserializeDBValue(BinaryDataRef bdr)
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredScriptHistory::getDBKey(bool withPrefix) const
{
   BinaryWriter bw(1+uniqueKey_.getSize());
   if(withPrefix)
      bw.put_uint8_t((uint8_t)DB_PREFIX_SCRIPT); 
   
   bw.put_BinaryData(uniqueKey_);
   return bw.getData();
}


////////////////////////////////////////////////////////////////////////////////
SCRIPT_PREFIX StoredScriptHistory::getScriptType(void) const
{
   if(uniqueKey_.getSize() == 0)
      return SCRIPT_PREFIX_NONSTD;
   else
      return (SCRIPT_PREFIX)uniqueKey_[0];
}


/////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::unserializeDBKey(BinaryDataRef key, bool withPrefix)
{
   // Assume prefix
   if(withPrefix)
      uniqueKey_ = key.getSliceCopy(1, key.getSize()-1);
   else
      uniqueKey_ = key;
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::pprintOneLine(uint32_t indent)
{
   for(uint32_t i=0; i<indent; i++)
      cout << " ";

   string ktype;
   if(uniqueKey_[0] == SCRIPT_PREFIX_HASH160)
      ktype = "H160";
   else if(uniqueKey_[0] == SCRIPT_PREFIX_P2SH)
      ktype = "P2SH";
   else if(uniqueKey_[0] == SCRIPT_PREFIX_MULTISIG)
      ktype = "MSIG";
   else if(uniqueKey_[0] == SCRIPT_PREFIX_NONSTD)
      ktype = "NSTD";
   
   uint32_t sz = uniqueKey_.getSize();
   cout << "SSHOBJ: " << ktype.c_str() << ": "
        << uniqueKey_.getSliceCopy(1,sz-1).toHexStr()
        << " Sync: " << scanHeight_ 
        << " #IO: " << totalTxioCount_
        << " Unspent: " << (totalUnspent_/COIN)
        << endl;
}


////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::pprintFullSSH(uint32_t indent)
{
   pprintOneLine(indent);

   // Print all the txioVects
   map<BinaryData, StoredSubHistory>::iterator iter;
   for(iter = subHistMap_.begin(); iter != subHistMap_.end(); iter++)
      iter->second.pprintFullSubSSH(indent+3);
}

////////////////////////////////////////////////////////////////////////////////
bool StoredScriptHistory::haveFullHistoryLoaded(void) const
{
   //Shouldn't be using this call outside of C++ unit tests. It is supported to
   //accomodate for unit tests degree of data review, but it is painfully slow
   //and should be avoided in all speed critical operations. The method already
   //assumes we function in an environment with full history in ram, which
   //doesn't with the new backend anymore.

   if(!isInitialized())
      return false;

   uint64_t numTxio = 0;
   map<BinaryData, StoredSubHistory>::const_iterator iter;
   for (iter = subHistMap_.begin(); iter != subHistMap_.end(); iter++)
   {
      for (const auto& txioPair : iter->second.txioMap_)
      {
         if (txioPair.second.isUTXO())
            numTxio++;
         else if (txioPair.second.hasTxIn())
            numTxio += 2;
      }
   }

   if(numTxio > totalTxioCount_)
      LOGERR << "Somehow stored total is less than counted total...?";

   return (numTxio==totalTxioCount_);
}

////////////////////////////////////////////////////////////////////////////////
uint64_t StoredScriptHistory::getScriptReceived(bool withMultisig)
{
   if(!haveFullHistoryLoaded())
      return UINT64_MAX;

   uint64_t bal = 0;
   map<BinaryData, StoredSubHistory>::iterator iter;
   for(iter = subHistMap_.begin(); iter != subHistMap_.end(); iter++)
      bal += iter->second.getSubHistoryReceived(withMultisig);

   return bal;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t StoredScriptHistory::getScriptBalance(bool withMultisig)
{
   // If regular balance, 
   if(!withMultisig)
      return totalUnspent_;

   // If with multisig we have to load and count everything
   if(!haveFullHistoryLoaded())
      return UINT64_MAX;

   uint64_t bal = 0;
   map<BinaryData, StoredSubHistory>::iterator iter;
   for(iter = subHistMap_.begin(); iter != subHistMap_.end(); iter++)
      bal += iter->second.getSubHistoryBalance(withMultisig);

   return bal;
}

////////////////////////////////////////////////////////////////////////////////
bool StoredScriptHistory::getFullTxioMap( map<BinaryData, TxIOPair> & mapToFill,
                                          bool withMultisig)
{
   if(!haveFullHistoryLoaded())
      return false;

   map<BinaryData, StoredSubHistory>::iterator iterSubSSH;
   for(iterSubSSH  = subHistMap_.begin(); 
       iterSubSSH != subHistMap_.end(); 
       iterSubSSH++)
   {
      StoredSubHistory & subssh = iterSubSSH->second;

      if(withMultisig)
      {
         // If with multisig, we can just copy everything
         mapToFill.insert(subssh.txioMap_.begin(), subssh.txioMap_.end());
      }
      else
      {
         // Otherwise, we have to filter out the multisig TxIOs
         map<BinaryData, TxIOPair>::iterator iterTxio;
         for(iterTxio  = subssh.txioMap_.begin();
             iterTxio != subssh.txioMap_.end();
             iterTxio++)
         {
            if(!iterTxio->second.isMultisig())
               mapToFill[iterTxio->first] = iterTxio->second;
         }
         
      }
   }
   return true;
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::mergeSubHistory(const StoredSubHistory& subssh)
{
   auto& subSshEntry = subHistMap_[subssh.hgtX_];
   if (!subSshEntry.isInitialized())
   {
      subSshEntry = subssh;
      return;
   }

   for (const auto& txioPair : subssh.txioMap_)
      subSshEntry.txioMap_.insert(txioPair);
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::insertTxio(const TxIOPair& txio)
{
   auto& subSshEntry = subHistMap_[txio.getDBKeyOfOutput().getSliceRef(0, 4)];
   if (!subSshEntry.isInitialized())
   {
      subSshEntry.uniqueKey_ = uniqueKey_;
      subSshEntry.hgtX_      = txio.getDBKeyOfOutput().getSliceCopy(0, 4);
   }

   auto wasInserted = subSshEntry.txioMap_.insert({ txio.getDBKeyOfOutput(), txio });

   if (wasInserted.second == true)
   {
      if (!txio.hasTxIn() && !txio.isMultisig())
         totalUnspent_ += txio.getValue();
      totalTxioCount_++;
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::eraseTxio(const TxIOPair& txio)
{
   auto& subSshEntry = subHistMap_[txio.getDBKeyOfOutput().getSliceRef(0, 4)];

   auto wasRemoved = subSshEntry.txioMap_.erase(txio.getDBKeyOfOutput());

   if (wasRemoved == 1)
   {
      if (!txio.hasTxIn() && !txio.isMultisig())
         totalUnspent_ -= txio.getValue();
      totalTxioCount_--;
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredScriptHistory::clear()
{
   uniqueKey_.clear();
   version_ = UINT32_MAX;
   scanHeight_ = tallyHeight_ = -1;

   totalTxioCount_ = totalUnspent_ = 0;

   subsshSummary_.clear();
   subHistMap_.clear();
}

////////////////////////////////////////////////////////////////////////////////
// SubSSH object code
//
// If the ssh has more than one TxIO, then we put them into SubSSH objects,
// which represent a list of TxIOs for the given block.  The complexity of
// doing it this way seems unnecessary, but it actually works quite efficiently
// for massively-reused addresses like SatoshiDice.
////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::unserializeDBValue(BinaryRefReader & brr)
{
   // Get the TxOut list if a pointer was supplied
   // This list is unspent-TxOuts only if pruning enabled.  You will
   // have to dereference each one to check spentness if not pruning
   if(hgtX_.getSize() != 4)
   {
      LOGERR << "Cannot unserialize DB value until key is set (hgt&dup)";
      uniqueKey_.resize(0);
      return;
   }

   BinaryData fullTxKey(8);
   hgtX_.copyTo(fullTxKey.getPtr());

   txioCount_ = (uint32_t)(brr.get_var_int());
   for (uint32_t i = 0; i<txioCount_; i++)
   {
      BitUnpacker<uint8_t> bitunpack(brr);
      bool isFromSelf      = bitunpack.getBit();
      bool isCoinbase      = bitunpack.getBit();
      bool isSpent         = bitunpack.getBit();
      bool isMulti         = bitunpack.getBit();
      bool isUTXO          = bitunpack.getBit();

      // We always include the 8-byte value
      uint64_t txoValue  = brr.get_uint64_t();
      TxIOPair txio;
      txio.setValue(txoValue);
      txio.setUTXO(isUTXO);

      if (!isSpent)
      {
         // First 4 bytes is same for all TxIOs, and was copied outside the loop.
         // So we grab the last four bytes and copy it to the end.
         brr.get_BinaryData(fullTxKey.getPtr() + 4, 4);
         txio.setTxOut(fullTxKey);
      }
      else
      {
         //spent subssh, TxOut will always carry a full DBkey
         txio.setTxOut(brr.get_BinaryDataRef(8));

         //4 bytes entry
         brr.get_BinaryData(fullTxKey.getPtr() + 4, 4);
         txio.setTxIn(fullTxKey);
      }

      txio.setTxOutFromSelf(isFromSelf);
      txio.setFromCoinbase(isCoinbase);
      txio.setMultisig(isMulti);

      //insertTxio(txio);
      BinaryData key8B = txio.getDBKeyOfOutput();

      pair<BinaryData, TxIOPair> txioInsertPair(
         move(key8B), move(txio));
      txioMap_.insert(move(txioInsertPair));
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::getSummary(BinaryRefReader & brr)
{
   //grab subssh txioCount from DB
   if (hgtX_.getSize() != 4)
   {
      LOGERR << "Cannot unserialize DB value until key is set (hgt&dup)";
      uniqueKey_.resize(0);
      return;
   }

   BinaryData fullTxKey(8);
   hgtX_.copyTo(fullTxKey.getPtr());

   txioCount_ = (uint32_t)(brr.get_var_int());
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::serializeDBValue(BinaryWriter & bw, 
                                        LMDBBlockDatabase *db, 
                                        ARMORY_DB_TYPE dbType) const
{
   bw.put_var_int(txioMap_.size());
   for(const auto& txioPair : txioMap_)
   {
      TxIOPair const & txio = txioPair.second;
      bool isSpent = txio.hasTxInInMain(db);

      // If spent and only maintaining a pruned DB, skip it
      if(isSpent)
      {
         if(!txio.getTxRefOfInput().isInitialized())
         {
            LOGERR << "TxIO is spent, but input is not initialized";
            continue;
         }
      }

      BinaryData key8B = txio.getDBKeyOfOutput();
      if (isSpent)
         key8B = txio.getDBKeyOfInput();

      if (!key8B.startsWith(hgtX_))
        LOGERR << "How did TxIO key not match hgtX_??";


      BitPacker<uint8_t> bitpack;
      bitpack.putBit(txio.isTxOutFromSelf());
      bitpack.putBit(txio.isFromCoinbase());
      bitpack.putBit(txio.hasTxInInMain(db));
      bitpack.putBit(txio.isMultisig());
      bitpack.putBit(txio.isUTXO());
      bw.put_BitPacker(bitpack);

      if (!isSpent)
      {
         // Always write the value and last 4 bytes of dbkey (first 4 is in dbkey)
         bw.put_uint64_t(txio.getValue());
         bw.put_BinaryData(key8B.getSliceCopy(4, 4));
      }
      else
      {
         //spent subssh entry that marks the spent TxOut at the TxIn hgtX
         
         //write the full TxOut dbkey, since this is saved at TxIn hgtX
         bw.put_uint64_t(txio.getValue());
         bw.put_BinaryData(txio.getDBKeyOfOutput());

         //Spent subssh are saved by TxIn hgtX, only write the last 4 bytes
         bw.put_BinaryData(key8B.getSliceCopy(4, 4));
      }
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::unserializeDBValue(BinaryDataRef bdr)
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::unserializeDBKey(BinaryDataRef key, bool withPrefix)
{
   uint32_t sz = key.getSize();
   BinaryRefReader brr(key);
   
   // Assume prefix
   if(withPrefix)
   {
      DBUtils::checkPrefixByte(brr, DB_PREFIX_SCRIPT);
      sz -= 1;
   }

   brr.get_BinaryData(uniqueKey_, sz-4);
   brr.get_BinaryData(hgtX_, 4);

   uint8_t* hgtXptr = (uint8_t*)hgtX_.getPtr();
   height_ = 0;
   uint8_t* hgt = (uint8_t*)&height_;

   dupID_ = hgtXptr[3];
   hgt[0] = hgtXptr[2];
   hgt[1] = hgtXptr[1];
   hgt[2] = hgtXptr[0];
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredSubHistory::getDBKey(bool withPrefix) const
{
   BinaryWriter bw;
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_SCRIPT);

   bw.put_BinaryData(uniqueKey_);
   bw.put_BinaryData(hgtX_);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
SCRIPT_PREFIX StoredSubHistory::getScriptType(void) const
{
   if(uniqueKey_.getSize() == 0)
      return SCRIPT_PREFIX_NONSTD;
   else
      return (SCRIPT_PREFIX)uniqueKey_[0];
}

////////////////////////////////////////////////////////////////////////////////
void StoredSubHistory::pprintFullSubSSH(uint32_t indent)
{
   for(uint32_t ind=0; ind<indent; ind++)
      cout << " ";

   uint32_t hgt = DBUtils::hgtxToHeight(hgtX_);
   uint8_t  dup = DBUtils::hgtxToDupID(hgtX_);
   cout << "SubSSH: " << hgtX_.toHexStr().c_str();
   cout << " Hgt&Dup: (" << hgt << "," << (uint32_t)dup << ")" << endl;

   // Print all the txioVects
   map<BinaryData, TxIOPair>::iterator iter;
   for(iter = txioMap_.begin(); iter != txioMap_.end(); iter++)
   {
      for(uint32_t ind=0; ind<indent+3; ind++)
         cout << " ";

      TxIOPair & txio = iter->second;
      uint32_t _hgt;
      uint8_t  _dup;
      uint16_t txi;
      uint16_t txo = txio.getIndexOfOutput();
      BinaryData txoKey = txio.getDBKeyOfOutput();
      BinaryRefReader brrTxOut(txoKey);
      DBUtils::readBlkDataKeyNoPrefix(brrTxOut, _hgt, _dup, txi);
      cout << "TXIO: (" << _hgt << "," << (uint32_t)_dup 
                          << "," << txi << "," << txo << ")";

      
      cout << " VALUE: " << (txio.getValue() /COIN);
      cout << " isCB: " << (txio.isFromCoinbase() ? "X" : " ");
      cout << " isMS: " << (txio.isMultisig() ? "X" : " ");
      cout << " Type: " << (uint32_t)uniqueKey_[0];
      cout << " Addr: " << uniqueKey_.getSliceCopy(1,4).toHexStr().c_str();

      if(txio.hasTxIn())
      {
         uint16_t _txo = txio.getIndexOfInput();
         BinaryData txiKey = txio.getDBKeyOfInput();
         BinaryRefReader brrTxIn(txiKey);
         DBUtils::readBlkDataKeyNoPrefix(brrTxIn, _hgt, _dup, txi);
         cout << "  SPENT: (" << _hgt << "," << (uint32_t)_dup 
                       << "," << txi << "," << _txo << ")";
      }
      cout << endl;
   }
   

}

////////////////////////////////////////////////////////////////////////////////
uint64_t StoredSubHistory::getSubHistoryReceived(bool withMultisig)
{
   uint64_t bal = 0;
   map<BinaryData, TxIOPair>::iterator iter;
   for (iter = txioMap_.begin(); iter != txioMap_.end(); iter++)
   {
      if (iter->second.isUTXO() && (!iter->second.isMultisig() || withMultisig))
         bal += iter->second.getValue();
      else if (iter->second.hasTxIn())
         bal += iter->second.getValue();
   }
   return bal;
}

////////////////////////////////////////////////////////////////////////////////
uint64_t StoredSubHistory::getSubHistoryBalance(bool withMultisig)
{
   uint64_t bal = 0;
   map<BinaryData, TxIOPair>::iterator iter;
   for (iter = txioMap_.begin(); iter != txioMap_.end(); iter++)
   {
      if (!iter->second.hasTxIn())
      if (!iter->second.isMultisig() || withMultisig)
         bal += iter->second.getValue();
   }
   return bal;
}
////////////////////////////////////////////////////////////////////////////////
// This method will add the TxIOPair to the ssh object if it doesn't exist,
// in addition to marking it unspent.  
//
// If there is a 2-of-3 multisig scraddr M, which includes pubkeys, X, Y and Z,
// then the DB will ultimately look like this:
//
//    Key:                       Value:
//    -------                    -------
//    PREFIX_SCRIPT + M          TxIO.isMultisigRef == false
//    PREFIX_SCRIPT + X          TxIO.isMultisigRef == true
//    PREFIX_SCRIPT + Y          TxIO.isMultisigRef == true
//    PREFIX_SCRIPT + Z          TxIO.isMultisigRef == true
//    
// We will ultimately update all four entries, but the TxIOs that are added
// to X, Y and Z will be flagged so they are not interpretted as single-sig
// addresses.  We do this so we can later lookup multi-sig addresses that 
// involve a given scraddr, but don't automatically include them in any
// balance or UTXO set calculations.
//   
// Returns the difference to be applied to totalUnspent_ in the outer ssh
// (unless it's UINT64_MAX which is interpretted as failure)
void StoredSubHistory::markTxOutUnspent(const BinaryData& txOutKey8B, 
                                        uint64_t&  additionalSize,
                                        const uint64_t&  value,
                                        bool       isCoinbase,
                                        bool       isMultisigRef)
{
   TxIOPair& txio = txioMap_[txOutKey8B];
   if(!txio.hasTxOut())
   {
      // The TxIOPair was not in the subSSH yet;  add it
      txio.setTxOut(txOutKey8B);
      txio.setValue(value);
      txio.setFromCoinbase(isCoinbase);
      txio.setMultisig(isMultisigRef);
      txio.setUTXO(true);
      
      additionalSize += sizeof(TxIOPair)+8;
   }
   else
   {
      txio.setTxIn(TxRef(), UINT32_MAX);
      txio.setUTXO(true);
   }
}

/* Meh, no demand for this functionality yet ... finish it later
////////////////////////////////////////////////////////////////////////////////
// One loop to compute all four values
//    values[0] ~ current balance no multisig
//    values[1] ~ current balance multisig-only
//    values[2] ~ total received  no multisig
//    values[3] ~ total received  multisig-only
vector<uint64_t> StoredSubHistory::getSubHistoryValues(void)
{
   //
   vector<uint64_t> values(4);
   for(uint32_t i=0; i<4; i++)
      values[i] = 0;

   map<BinaryData, TxIOPair>::iterator iter;
   for(iter = txioSet_.begin(); iter != txioSet_.end(); iter++)
   {
      if(iter->second.isMultisig())
      {
         
      }
      if(!iter->second.hasTxIn())
         if(!iter->second.isMultisig() || withMultisig)
            bal += iter->second.getValue();
   }
   return bal;
}
*/

////////////////////////////////////////////////////////////////////////////////
void StoredUndoData::unserializeDBValue(BinaryRefReader & brr, 
   ARMORY_DB_TYPE dbType)
{
   brr.get_BinaryData(blockHash_, 32);

   uint32_t nStxoRmd = brr.get_uint32_t();
   stxOutsRemovedByBlock_.clear();
   stxOutsRemovedByBlock_.resize(nStxoRmd);

   for(uint32_t i=0; i<nStxoRmd; i++)
   {
      StoredTxOut & stxo = stxOutsRemovedByBlock_[i];

      // Store the standard flags that go with StoredTxOuts, minus spentness
      BitUnpacker<uint8_t> bitunpack(brr);
      stxo.unserDbType_ = bitunpack.getBits(4);
      stxo.txVersion_   = bitunpack.getBits(2);
      stxo.isCoinbase_  = bitunpack.getBit();

      BinaryData hgtx   = brr.get_BinaryData(4);
      stxo.blockHeight_ = DBUtils::hgtxToHeight(hgtx);
      stxo.duplicateID_ = DBUtils::hgtxToDupID(hgtx);
      stxo.txIndex_     = brr.get_uint16_t(BE);
      stxo.txOutIndex_  = brr.get_uint16_t(BE);

      // This is the raw OutPoint of the removed TxOut.  May not strictly
      // be necessary for processing undo ops in this DB (but might be), 
      // but may be useful for giving to peers if needed w/o exta lookups
      brr.get_BinaryData(stxo.parentHash_, 32);
      stxo.txOutIndex_ = brr.get_uint32_t();
   
      // Then read the raw TxOut itself
      stxo.unserialize(brr);
   }

   uint32_t nOpAdded = brr.get_uint32_t();
   outPointsAddedByBlock_.clear();
   outPointsAddedByBlock_.resize(nStxoRmd);
   for(uint32_t i=0; i<nOpAdded; i++)
      outPointsAddedByBlock_[i].unserialize(brr);
    
}

////////////////////////////////////////////////////////////////////////////////
void StoredUndoData::serializeDBValue(
   BinaryWriter & bw, ARMORY_DB_TYPE dbType) const
{
   bw.put_BinaryData(blockHash_);

   uint32_t nStxoRmd = stxOutsRemovedByBlock_.size();
   uint32_t nOpAdded = outPointsAddedByBlock_.size();


   // Store the full TxOuts that were removed... since they will have been
   // removed from the DB and have to be fully added again if we undo the block
   bw.put_uint32_t(nStxoRmd);
   for(uint32_t i=0; i<nStxoRmd; i++)
   {
      StoredTxOut const & stxo = stxOutsRemovedByBlock_[i];

      if(stxo.parentHash_.getSize() == 0          || 
         stxo.txOutIndex_           == UINT16_MAX   )
      {
         LOGERR << "Can't write undo data w/o parent hash and/or TxOut index";
         return;
      }

      // Store the standard flags that go with StoredTxOuts, minus spentness
      BitPacker<uint8_t> bitpack;
      bitpack.putBits( (uint8_t)dbType,  4);
      bitpack.putBits( (uint8_t)stxo.txVersion_,            2);
      bitpack.putBit(           stxo.isCoinbase_);

      bw.put_BitPacker(bitpack);

      // Put the blkdata key directly into the DB to save us a lookup 
      bw.put_BinaryData( DBUtils::getBlkDataKeyNoPrefix( stxo.blockHeight_,
                                                        stxo.duplicateID_,
                                                        stxo.txIndex_,
                                                        stxo.txOutIndex_));

      bw.put_BinaryData(stxo.parentHash_);
      bw.put_uint32_t((uint32_t)stxo.txOutIndex_);
      bw.put_BinaryData(stxo.getSerializedTxOut());
   }

   // Store just the OutPoints of the TxOuts that were added by this block.
   // If we're undoing this block, we have the full TxOuts already in the DB
   // under the block key with same hgt & dup.   We could probably avoid 
   // storing this data at all due to this DB design, but it is needed if we
   // are ever going to serve any other process that expects the OutPoint list.
   bw.put_uint32_t(nOpAdded);
   for(uint32_t i=0; i<nOpAdded; i++)
      bw.put_BinaryData(outPointsAddedByBlock_[i].serialize()); 
}

////////////////////////////////////////////////////////////////////////////////
void StoredUndoData::unserializeDBValue(
   BinaryData const & bd, ARMORY_DB_TYPE dbType)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr, dbType);
}

////////////////////////////////////////////////////////////////////////////////
void StoredUndoData::unserializeDBValue(
   BinaryDataRef bdr, ARMORY_DB_TYPE dbType)
                                  
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr, dbType);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredUndoData::getDBKey(bool withPrefix) const
{
   if(!withPrefix)
      return DBUtils::getBlkDataKeyNoPrefix(blockHeight_, duplicateID_);
   else
   {
      BinaryWriter bw(5);
      bw.put_uint8_t((uint8_t)DB_PREFIX_UNDODATA); 
      bw.put_BinaryData( DBUtils::getBlkDataKeyNoPrefix(blockHeight_, duplicateID_));
      return bw.getData();
   }
}


////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void StoredTxHints::unserializeDBValue(BinaryRefReader & brr)
{
   uint64_t numHints = (brr.getSizeRemaining()==0 ? 0 : brr.get_var_int());
   dbKeyList_.resize((uint32_t)numHints);
   for(uint32_t i=0; i<numHints; i++)
      brr.get_BinaryData(dbKeyList_[i], 6);

   // Preferred simply means it's supposed to be first in the list
   // This simply improves search time in the event there's multiple hints
   if(numHints > 0)
      preferredDBKey_ = dbKeyList_[0];
}


////////////////////////////////////////////////////////////////////////////////
void StoredTxHints::serializeDBValue(BinaryWriter & bw ) const
{
   bw.put_var_int(dbKeyList_.size());
   
   // Find and write the preferred key first, skip all unpreferred (the first
   // one in the list is the preferred key... that paradigm could be improved
   // for sure...)
   for(uint32_t i=0; i<dbKeyList_.size(); i++)
   {
      if(dbKeyList_[i] != preferredDBKey_)
         continue;

      bw.put_BinaryData(dbKeyList_[i]);
      break;
   }

   // Now write all the remaining keys in whatever order they are naturally
   // sorted (skip the preferred key since it was already written)
   for(uint32_t i=0; i<dbKeyList_.size(); i++)
   {
      if(dbKeyList_[i] == preferredDBKey_)
         continue;

      bw.put_BinaryData(dbKeyList_[i]);
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxHints::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxHints::unserializeDBValue(BinaryDataRef bdr)
                                  
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxHints::serializeDBValue(void) const
{
   BinaryWriter bw;
   serializeDBValue(bw);
   return bw.getData();
}


////////////////////////////////////////////////////////////////////////////////
BinaryData StoredTxHints::getDBKey(bool withPrefix) const
{
   if(!withPrefix)
      return txHashPrefix_;
   else
   {
      BinaryWriter bw(5);
      bw.put_uint8_t((uint8_t)DB_PREFIX_TXHINTS); 
      bw.put_BinaryData( txHashPrefix_);
      return bw.getData();
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredTxHints::unserializeDBKey(BinaryDataRef key, bool withPrefix)
{
   if(withPrefix)
      txHashPrefix_ = key.getSliceCopy(1, 4);
   else
      txHashPrefix_ = key;
}

////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
void StoredHeadHgtList::unserializeDBValue(BinaryRefReader & brr)
{
   uint32_t numHeads = brr.get_uint8_t();
   dupAndHashList_.resize(numHeads);
   preferredDup_ = UINT8_MAX;
   for(uint32_t i=0; i<numHeads; i++)
   {
      uint8_t dup = brr.get_uint8_t();
      dupAndHashList_[i].first = dup & 0x7f;
      brr.get_BinaryData(dupAndHashList_[i].second, 32);
      if((dup & 0x80) > 0)
         preferredDup_ = dup & 0x7f;
   }
}

////////////////////////////////////////////////////////////////////////////////
void StoredHeadHgtList::serializeDBValue(BinaryWriter & bw ) const
{
   bw.put_uint8_t( dupAndHashList_.size() );

   // Write the preferred/valid block header first
   for(uint32_t i=0; i<dupAndHashList_.size(); i++)
   {
      if(dupAndHashList_[i].first != preferredDup_)
         continue; 

      bw.put_uint8_t(dupAndHashList_[i].first | 0x80);
      bw.put_BinaryData(dupAndHashList_[i].second);
      break;
   }
         
   // Now write everything else
   for(uint32_t i=0; i<dupAndHashList_.size(); i++)
   {
      if(dupAndHashList_[i].first == preferredDup_)
         continue; 

      bw.put_uint8_t(dupAndHashList_[i].first & 0x7f);
      bw.put_BinaryData(dupAndHashList_[i].second);
   }

}

////////////////////////////////////////////////////////////////////////////////
void StoredHeadHgtList::unserializeDBValue(BinaryData const & bd)
{
   BinaryRefReader brr(bd);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
void StoredHeadHgtList::unserializeDBValue(BinaryDataRef bdr)
                                  
{
   BinaryRefReader brr(bdr);
   unserializeDBValue(brr);
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredHeadHgtList::serializeDBValue(void) const
{
   BinaryWriter bw;
   serializeDBValue(bw);
   return bw.getData();
}

////////////////////////////////////////////////////////////////////////////////
BinaryData StoredHeadHgtList::getDBKey(bool withPrefix) const
{
   BinaryWriter bw(5);
   if(withPrefix)
      bw.put_uint8_t((uint8_t)DB_PREFIX_HEADHGT); 
   bw.put_uint32_t(height_, BE);
   return bw.getData();

}

////////////////////////////////////////////////////////////////////////////////
void StoredHeadHgtList::unserializeDBKey(BinaryDataRef key)
{
   BinaryRefReader brr(key);
   if(key.getSize() == 5)
   {
      uint8_t prefix = brr.get_uint8_t();
      if(prefix != DB_PREFIX_HEADHGT)  
      {
         LOGERR << "Unserialized HEADHGT key but wrong prefix";
         return;
      }
   }

   height_ = brr.get_uint32_t(BE);
}

// kate: indent-width 3; replace-tabs on;
