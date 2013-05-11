#include <iostream>
#include <sstream>
#include "leveldb_wrapper.h"



////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////
//
// STORED HEADER/TX/TXOUT Methods
//
////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////

//StoredBlockHeader::StoredBlockHeader


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
BinaryData StoredBlockHeader::getFullBlock(void)
{
   if(!haveFullBlock())
      return BinaryData(0);

   BinaryWriter bw;
   bw.put_BinaryData(dataCopy_); 
   bw.put_var_int(numTx_);
   for(uint32_t tx=0; tx<numTx_; tx++)
      bw.put_BinaryData(txMap_[tx].getSerializedTx());
   
   return bw.getData();
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
      cerr << "ERROR:  can't serialize an uninitialized header!" << endl;
      return;
   }

   if(merkType==MERKLE_SER_FULL && txMap_.size() < numTx_)
   {
      cerr << "ERROR:  Cannot produce full tx list" << endl;
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
         bw.put_BinaryData(iter->second.thisHash_)
      }
   }
   
   
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
      cerr << "ERROR: creating storedtx from uninitialized tx" << endl;
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


////////////////////////////////////////////////////////////////////////////////
// The dbType and pruneType inputs are left blank if you are just going to take 
// whatever is the current state of database.  You can choose to manually 
// specify them, if you want to throw an error if it's not what you were 
// expecting
InterfaceToLevelDB::InterfaceToLevelDB(
                   string basedir, BinaryData const & genesisBlkHash, 
                   BinaryData const & genesisTxHash, 
                   BinaryData const & magic,
                   ARMORY_DB_TYPE     dbtype=ARMORY_DB_WHATEVER,
                   DB_PRUNE_TYPE      pruneType=DB_PRUNE_WHATEVER)
{
   baseDir_ = basedir;
   char dbname[1024];

   stringstream head;
   head << baseDir_ << "/" << "leveldb_headers";
   dbPaths_[0] = head.str();

   stringstream blk;
   blk << baseDir_ << "/" << "leveldb_blkdata";
   dbPaths_[1] = blk.str();
   
   magicBytes_ = magic;
   genesisTxHash_ = genesisTxHash;
   genesisBlkHash_ = genesisBlkHash;

   armoryDbType_ = dbtype;
   dbPruneType_  = pruneType;

   // Open databases and check that everything is correct
   // Or create the databases and start it up
   openDatabases();
}



/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txOutScriptToLevelDBKey(BinaryData const & script)
{
   BinaryWriter bw;
   bw.put_uint8_t(DB_PREFIX_REGADDR);

   TXOUT_SCRIPT_TYPE scrType = getTxOutScriptType(script.getRef());
   
   bw.put_var_int(script.getSize()) ;
   bw.put_BinaryData(script.getRef());
   return bw.getData();
}



/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::headerHashToLevelDBKey(BinaryData const & headHash)
{
   BinaryWriter bw;
   bw.put_uint8_t(DB_PREFIX_HEADERS);
   bw.put_BinaryData(headHash);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txHashToLevelDBKey(BinaryData const & txHash)
{
   // We actually only store the first four bytes of the tx
   BinaryWriter bw;
   bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_BinaryData(txHash, 0, 4);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::openDatabases(void)
{
   if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      cerr << "***ERROR:  must set magic bytes and genesis block" << endl;
      cerr << "           before opening databases."  << endl;
      return false;
   }

   // Just in case this isn't the first time we tried to open it.
   closeDatabases();

   vector<leveldb::DB*> dbs[2];
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      leveldb::Options opts;
      opts.create_if_missing = true;
      //opts2.compression        = leveldb::kNoCompression;
      //opts2.filter_policy      = leveldb::NewBloomFilter(10);
      checkStatus(leveldb::DB::Open(opts2, dbPaths_[db],  &dbs_[db]));

      // Create an iterator that we'll use for ust about all DB seek ops
      iters_[db] = dbs_[db]->NewIterator(leveldb::ReadOptions());
      batches_[db] = NULL;
         
      BinaryData dbInfo = getValue(dbs_[db], getDBInfoKey());
      if(dbInfo.getSize() == 0)
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         uint32_t flagBytes = 0;
         flagBytes |= (uint32_t)ARMORY_DB_VERSION << 28;
         flagBytes |= (uint32_t)armoryDbType_ << 24;
         flagBytes |= (uint32_t)dbPruneType_ << 20;

         BinaryWriter bw;
         bw.put_uint32_t(ARMORY_DB_VERSION)
         bw.put_BinaryData(magicBytes_);
         bw.put_uint32_t(flagBytes);
         bw.put_uint32_t(0);
         bw.put_BinaryData(genesisBlkHash_);
   
         putValue(dbs_[db], getDBInfoKey(), bw.getData());
      }
      else
      {
         // Else we read the DB info and make sure everything matches up
         if(dbinfo.getSize() < 40)
         {
            cerr << "***ERROR: Invalid DatabaseInfo data" << endl;
            closeDatabases();
            return false;
         }
         BinaryReader br(dbinfo);
         uint32_t version = br.get_uint32_t();
         BinaryData magic = br.get_BinaryData(4);
         uint32_t flags   = br.get_uint32_t();
         topBlockHeight_  = br.get_uint32_t();
         topBlockHash_    = br.get_BinaryData(32);
      
         // Check that the magic bytes are correct
         if(magicBytes_ != magic)
         {
            cerr << "***ERROR:  Magic bytes mismatch!  Different blkchain?" << endl;
            closeDatabases();
            return false;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValue(dbs_[db], topBlockHash_).getSize() == 0 )
         {
            cerr << "***ERROR:  Top block doesn't exist!" << endl;
            closeDatabases();
            return false;
         }

         uint32_t dbVer      = (flags & 0xf0000000) >> 28;
         uint32_t dbType     = (flags & 0x0f000000) >> 24;
         uint32_t pruneType  = (flags & 0x00f00000) >> 20;

         if(armoryDbType_ == ARMORY_DB_WHATEVER)
            armoryDbType_ = (ARMORY_DB_TYPE)dbType;
         else if(armoryDbType_ != dbType)
         {
            cerr << "***ERROR: Mismatch in DB type" << endl;
            closeDatabases();
            return false;
         }

         if(dbPruneType_ == DB_PRUNE_WHATEVER)
            dbPruneType_ = (DB_PRUNE_TYPE)pruneType;
         else if(dbPruneType_ != pruneType)
         {
            cerr << "***ERROR: Mismatch in DB type" << endl;
            closeDatabases();
            return false;
         }
      }
   }

   // Now read all the RegisteredAddress objects to make it easy to query
   // inclusion directly from RAM.
   leveldb::Iterator* iter = iters_[BLKDATA];
   seekTo(BLKDATA, DB_PREFIX_REGADDR, BinaryData(0))
   lowestScannedUpTo_ = UINT32_MAX;
   while(iter->Valid())
   {
      if(currReadKey_.get_uint8_t() != (uint8_t)DB_PREFIX_REGADDR)
         break;

      RegisteredAddress ra;
      readRegisteredAddr(ra);
      registeredAddrSet_.insert(ra);
      lowestScannedUpTo_ = min(lowestScannedUpTo_, ra.alreadyScannedUpToBlk_);
   }

   return true;
}



/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void InterfaceToLevelDB::closeDatabases(void)
{
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      if( dbs_[db] != NULL)
         delete dbs_[db];
      
      if( batches_[db] != NULL )
         delete batches_[db];
   }
}

////////////////////////////////////////////////////////////////////////////////
// All put/del ops will be batched/queued, and only executed when commitBatch()
void InterfaceToLevelDB::startBatch(DB_SELECT db)
{
   if(batches_[db]==NULL)
      batches_[db] = new WriteBatch;

   batches_[db]->Clear();
}

////////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
void InterfaceToLevelDB::commitBatch(DB_SELECT db, doSync=false)
{
   if(batches_[db] == NULL)
   {
      cerr << "***ERROR:  Can't commit NULL WriteBatch" << endl;
      return;
   }
   leveldb::WriteOptions writeopt;
   writeopt.sync = doSync;
   leveldb::Status stat = dbs_[db]->Write(writeopt, batches_[db]);
   checkStatus(stat);

   batches_[db]->Clear();
   delete batches_[db];
   batches_[db] = NULL;
}

/////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, leveldb::Slice ldbKey)
{
   leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbKey, &lastGetValue_);
   if(stat==Status::IsNotFound())
      return BinaryData(0);

   checkStatus(stat);
   return BinaryData(value);
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, BinaryData const & key)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   return getValue(db, ldbKey)
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, BinaryDataRef key)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   return getValue(db, ldbKey)
}


/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, 
                                        DB_PREFIX prefix,
                                        BinaryData const & key)
{
   return getValue(db, prefix, key.getRef());
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryData object.  If you have a string, you can use
// BinaryData key(string(theStr));
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, 
                                        DB_PREFIX prefix,
                                        BinaryDataRef key)
{
   BinaryData keyFull(key.size()+1);
   keyFull[0] = (uint8_t)prefix;
   key.copyTo(keyFull.getPtr()+1, key.getSize());
   leveldb::Slice ldbKey((char*)keyFull.getPtr(), keyFull.getSize());
   return getValue(db, ldbKey)
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  Remember, references are only valid
// for as long as the iterator stays in one place.  If you want to collect 
// lots of values from the database, you must make copies of them using reg
// getValue() calls.
BinaryDataRef InterfaceToLevelDB::getValueRef(DB_SELECT db, BinaryData const & key)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   return getValue(db, ldbKey)

   leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbKey, &lastGetValue_);
   if(stat==Status::IsNotFound())
      lastGetValue_ = string("");

   return BinaryDataRef(lastGetValue_.data(), lastGetValue_.size());
}

/////////////////////////////////////////////////////////////////////////////
// Get value using BinaryDataRef object.  Remember, references are only valid
// for as long as the iterator stays in one place.  If you want to collect 
// lots of values from the database, you must make copies of them using reg
// getValue() calls.
BinaryDataRef InterfaceToLevelDB::getValueRef(DB_SELECT db, 
                                              DB_PREFIX prefix, 
                                              BinaryData const & key)
{
   if(db==HEADERS)
      return getValueRef(db, key);
   else
   {
      BinaryData ldbkey(key.getSize()+1)
      ldbkey[0] = (uint8_t)prefix;
      key.copyTo(ldbkey.getPtr()+1, key.getSize());
      return getValueRef(db, ldbkey);
   }
   
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLevelDB::putValue(DB_SELECT db, 
                                  BinaryData const & key, 
                                  BinaryData const & value)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   leveldb::Slice ldbVal((char*)value.getPtr(), value.getSize());
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, &value);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(leveldb::ReadOptions(), ldbkey, &value);
      checkStatus(stat);
   }
}


/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLevelDB::deleteValue(DB_SELECT db, 
                                     BinaryData const & key)
                 
{
   string value;
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, &value);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(leveldb::ReadOptions(), ldbkey, &value);
      checkStatus(stat);
   }
}


/////////////////////////////////////////////////////////////////////////////
// Not sure why this is useful over getHeaderMap() ... this iterates over
// the headers in hash-ID-order, instead of height-order
void InterfaceToLevelDB::startHeaderIteration()
{
   iterHeaders_ = dbs_[HEADERS]->NewIterator(leveldb::ReadOptions());
   iterHeaders_->SeekToFirst();

   // Skip the first entry which is the DatabaseInfo key
   if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey )
      cerr << "***WARNING: How do we not have a DB info key?" << endl; 
   else
      iterHeaders_->Next()
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::startBlockIteration(void)
{
   char prefix = DB_PREFIX_BLKDATA;
   seekTo(BLKDATA, DB_PREFIX_BLKDATA, BinaryData(0));
   leveldb::Slice start(&prefix, 1);
   iters_[BLKDATA] = dbs_[BLKDATA]->NewIterator(leveldb::ReadOptions());
   iters_[BLKDATA]->Seek(start);
   iteratorToRefReaders(iters_[BLKDATA], currReadKey_, currReadValue_);
}


/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLevelDB::advanceToNextBlock(bool skip=false)
{
   char prefix = DB_PREFIX_BLKDATA;

   leveldb::Iterator* it = iters_[BLKDATA];
   BinaryData key;
   while(1) 
   {
      if(skip) it->Next();

      if( !it->Valid() || it->key()[0] != (char)DB_PREFIX_BLKDATA)
         return false;
      else if( it->key().size() == 5)
      {
         iteratorToRefReaders(it, currReadKey_, currReadValue_);
         return true;
      }

      if(!skip) it->Next()
   } 
   cerr << "ERROR: we should never get here..." << endl;
   return false;
}


void InterfaceToLevelDB::seekFirstRegAddr( levelbd::Iterator* it=NULL)
{
   if(it==NULL)
      it = iters_[BLKDATA];

   char prefix = DB_PREFIX_REGADDR;
   leveldb::Slice start(&prefix, 1);
   it.Seek(start);
}


/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::seekToRegAddr(BinaryData const & addr,
                                       leveldb::Iterator* it=NULL)
{
   if(it==NULL)
      it = iters_[BLKDATA];

   uint8_t prefix = DB_PREFIX_REGADDR;
   BianryData ldbkey = BinaryData(&prefix, 1) + addr;

   it.Seek(binaryDataToSlice(ldbkey));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   uint8_t itPrefix = currReadKey_.get_uint8_t();
   uint32_t sz = currReadKey_.getSize();
   if(itPrefix != prefix ||
      currReadKey_.get_BinaryDataRef(sz-1) != addr)
   {
      currReadKey_.resetPosition();
      return false;
   }

   currReadKey_.resetPosition();
   return true;
}

/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLevelDB::seekTo(DB_SELECT db,
                                BinaryData const & bd,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   it.Seek(binaryDataToSlice(bd));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   uint32_t sz = currReadKey_.getSize();
   bool isMatch = (currReadKey_.get_BinaryDataRef(sz)==bd);
   currReadKey_.resetPosition();
   return isMatch;
}

/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLevelDB::seekTo(DB_SELECT db,
                                DB_PREFIX prefix, 
                                BinaryData const & bd,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   BinaryData ldbkey;
   if(db==HEADERS)
      return seekTo(db, bd, it);
   else
   {
      uint8_t prefInt = (uint8_t)prefix;
      ldbkey = BinaryData(&prefInt, 1) + bd;
      return seekTo(db, ldbkey, it);
   }
}




/////////////////////////////////////////////////////////////////////////////
// Makes copies of the key and value
void InterfaceToLevelDB::iteratorToReaders( leveldb::Iterator* it, 
                                            BinaryReader & brKey,
                                            BinaryReader & brValue)
{
   brKey.setNewData(it->key().data(), it->key().size());      
   brValue;.setNewData(it->value().data(), it->value().size());      
}

/////////////////////////////////////////////////////////////////////////////
// Returns refs to key and value that become invalid when iterator is moved
void InterfaceToLevelDB::iteratorToRefReaders( leveldb::Iterator* it, 
                                               BinaryRefReader & brrKey,
                                               BinaryRefReader & brrValue)
{
   brrKey.setNewData(it->key().data(), it->key().size());      
   brrValue;.setNewData(it->value().data(), it->value().size());      
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlock( StoredBlockHeader & bh, 
                                    ignoreMerkle = true)
{
   bool isAnotherBlock = advanceToNextBlock();
   if(!isAnotherBlock)
   {
      cerr << "Tried to getBlock() but none left" << endl;
      return;
   }

    
   // Read the key for the block
   BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                          bh.blockHeight_,
                                          bh.duplicateID_);

   if(bdtype == NOT_BLKDATA)
   {
      cerr << "***ERROR: somehow did not advance to new block)";
      return; 
   }

   
   // Read the header and the extra data with it.
   readBlkDataHeaderValue(currReadValue_, bh, ignoreMerkle);
   
   for(uint32_t tx=0; tx<bh.numTx_; tx++)
   {
      advanceIterAndRead();
      uint32_t height;
      uint8_t  dupID;
      BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_, height, dupID);
      if(bdtype == BLKDATA_HEADER)
      {
         currReadKey_.resetPosition();
         break
      }

      currTxIndex = currReadKey_.get_uint16_t(); 
      if(index > txList().size())
      {
         cerr << "***ERROR:  Invalid index for tx at height " << (hgtX>>8)
              << " index " << index << endl;
         return;
      }

      if(bdtype == BLKDATA_TX)
      {
         bh.txMap_[currTxIndex] = Tx();
         readBlkDataTxValue(currReadValue_, bh.txMap_[currTxIndex]);
      }

      if(bdtype == BLKDATA_TXOUT)
      {
         currTxOutIndex = currReadKey_.get_uint16_t(); 
         readBlkDataTxOutValue(currReadValue_, txList[currTxIndex], currTxOutIndex);
      }
   }

      

}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataHeaderValue( 
                                 BinaryRefReader & brr,
                                 StoredBlockHeader & bh,
                                 bool ignoreMerkle)
{
   uint32_t flags = brr.get_uint32_t();
   bh.unserialize(brr);
   bh.storedNumTx_    = brr.get_uint32_t();
   bh.storedNumBytes_ = brr.get_uint32_t();


   uint8_t version             =                   (flags & 0xf0000000) >> 28;
   ARMORY_DB_TYPE dbtype       = (ARMORY_DB_TYPE)( (flags & 0x0f000000) >> 24);
   DB_PRUNE_TYPE pruneType     = (DB_PRUNE_TYPE)(  (flags & 0x00c00000) >> 22);
   MERKLE_SER_TYPE merkleCode  = (MERKLE_SER_TYPE)((flags & 0x00300000) >> 20);

   if(version != (uint8_t)ARMORY_DB_VERSION)
   {
      cerr << "Version mismatch in IFTLDB::getBlock()" << endl;
      advanceToNextBlock();
      return
   }

   if( !ignoreMerkle )
   {
      uint32_t currPos = brr.getPosition();
      uint32_t totalSz = brr.getSize();
      if(merkleCode == MERKLE_SER_NONE)
         bh.merkle_.resize(0);
      else
      {
         bh.merkleIsPartial_ = (merkleCode == MERKLE_SER_PARTIAL);
         brr.get_BinaryData(bh.merkle_, totalSz - currPos);
      }
      
   }
}

////////////////////////////////////////////////////////////////////////////////
BLKDATA_TYPE InterfaceToLevelDB::readBlkDataKey5B(
                                 BinaryRefReader & brr,
                                 uint32_t & height,
                                 uint8_t  & dupID)
{
   uint8_t  prefix = brr.get_uint8_t()
   if(prefix != DB_PREFIX_BLKDATA)
   {
      height = 0xffffffff;
      dupID  =       0xff;
      return NOT_BLKDATA;
   }
   
   uint32_t hgtX   = brr.get_uint32_t()
   height = hgtxToHeight(hgtX);
   dupID  = hgtxToDupID(hgtX);

   if(brr.getSizeRemaining() == 0)
      return BLKDATA_HEADER;
   else if(brr.getSizeRemaining() == 2)
      return BLKDATA_TX;
   else if(brr.getSizeRemaining() == 4)
      return BLKDATA_TXOUT;
   else
   {
      cerr << "Unexpected bytes remaining: " << brr.getSizeRemaining() << endl;
      return NOT_BLKDATA;
   }
}



////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxKey( BinaryRefReader & brr, StoredTx & tx)
{
   BLKDATA_TYPE bdtype = readBlkDataKey5B(brr, tx.storedHeight_, tx.storedDupID_);
   if(bdtype != DB_PREFIX_BLKDATA)
   {
      tx = StoredTx();
      return
   }

   tx.txIndex_ = brr.get_uint16_t()
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr, 
                                              StoredTxOut & txout)
{
   BLKDATA_TYPE bdt = readBlkDataKey5B(brr, txOut.blockHeight_, tx.blockDupID_);
   if(bdt != DB_PREFIX_BLKDATA)
      return

   txout.txIndex_    = brr.get_uint16_t();
   txout.txOutIndex_ = brr.get_uint16_t();
}

////////////////////////////////////////////////////////////////////////////////
StoredTxOut InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr)
{
   StoredTxOut txo;
   BLKDATA_TYPE bdt = readBlkDataKey5B(brr, txo.blockHeight_, txo.blockDupID_);
   if(bdt != DB_PREFIX_BLKDATA)
      return

   txo.txIndex_    = brr.get_uint16_t();
   txo.txOutIndex_ = brr.get_uint16_t();
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxValue( BinaryRefReader & brr, StoredTx& tx)
{
   uint16_t flags = brr.get_uint16_t();
   brr.get_BinaryData(tx.thisHash_, 32);

   // flags
   //    DBVersion      4 bits
   //    TxVersion      2 bits
   //    isValid        2 bits   (Unknown,  Valid, NotValid)
   //    HowTxSer       4 bits   (FullTxOut, TxNoTxOuts, numTxOutOnly)
   uint8_t dbVer   = (flags & 0xf000) >> 12;
   uint8_t txVer   = (flags & 0x0c00) >> 10;
   uint8_t isValid = (flags & 0x0300) >>  8;
   uint8_t txSer   = (flags & 0x00f0) >>  4;
   
   if(txSer == TX_SER_FULL || txSer == TX_SER_FRAGGED)
      tx.unserialize(brr, txSer==TX_SER_FRAGGED);
   else
      tx.numTxOut_ = brr.get_var_int();

   tx.version_ = (uint32_t)txVer;
   tx.isValid_ = isValid;
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxOutValue(BinaryRefReader & brr, 
                                               StoredTxOut & txOut)
{
   flags = brr.get_uint16_t();
   // Similar to TxValue flags
   //    DBVersion   4 bits
   //    TxVersion   2 bits
   //    isValid     2 bits
   //    Spentness   2 bits
   uint8_t dbVer   =  (flags & 0xf000) >> 12;
   uint8_t txVer   =  (flags & 0x0c00) >> 10; 
   uint8_t isValid =  (flags & 0x0300) >>  8; 
   uint8_t isSpent =  (flags & 0x00c0) >>  6; 
   txOut.unserialize(brr);
   txOut.storedIsSpent_ = isSpent;
   if(isSpent == TXOUT_SPENTSAV && brr.getSizeRemaining()>=6)
   {
      txOut.spentByHgtX_    = brr.get_uint32_t(); 
      txOut.spentByTxIndex_ = brr.get_uint16_t(); 
   }
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxOutValue(BinaryRefReader & brr, 
                                               Tx & tx, 
                                               uint32_t txOutIndex)
{
   readBlkDataTxOutValue(brr, tx.storedTxOuts_[txOutIndex]);
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readRegisteredAddr(RegisteredAddress & regAddr,
                                            vector<BinaryData>* txoVect=NULL,
                                            leveldb::Iterator* iter=NULL)
{
   if(iter==NULL)
      iter = iters_[BLKDATA];

   if(!iter->Valid())
   { 
      cerr << "Tried to access invalid iterator!" << endl;
      return;
   }

   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
    
   if( currReadKey_.get_uint8_t() != (uint8_t)DB_PREFIX_REGADDR)
   { 
      cerr << "Iterator does not point to a registered address" << endl;
      return;
   }
      
   uint32_t nBytes = currReadKey_.getSizeRemaining();
   regAddr.addrType_ = currReadKey_.get_uint8_t()
   currReadKey_.get_BinaryData(regAddr.uniqueKey_, nBytes);

   // Now read the stored data fro this registered address
   uint16_t flags = currReadValue_.get_uint16_t();
   regAddr.alreadyScannedUpToBlk_ = currReadValue_.get_uint32_t();
   regAddr.sumValue_ = currReadValue_.get_uint64_t();

    
   uint8_t version               =                   (flags & 0xf000) >> 12;
   DB_PRUNE_TYPE pruneType       = DB_PRUNE_TYPE(    (flags & 0x0c00) >> 10);
   REGADDR_UTXO_TYPE txoListType = REGADDR_UTXO_TYPE((flags & 0x0300) >>  8);
   

   if(txoListType == REGADDR_UTXO_TREE)
   {
      cerr << "***ERROR:  TXO-trees are not implemented, yet!" << endl;
      return;
   }
   else if(txoListType == REGADDR_UTXO_VECTOR)
   {
      // Get the TxOut list if a pointer was supplied
      // This list is unspent-TxOuts only if pruning enabled.  You will
      // have to dereference each one to check spentness if not pruning
      if(txoVect != NULL)
      {
         uint32_t numUtxo = (uint32_t)(currReadValue_.get_var_int());
         utxoVect.resize(numUtxo);
         for(uint32_t i=0; i<numUtxo; i++)
            utxoVect[i] = currReadValue_.get_BinaryData(8); 
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getUnspentTxOut( BinaryData & const ldbKey8B,
                                          UnspentTxOut & utxo)
{
   BinaryRefReader txrr(txoData[i]);
   uint32_t hgtX   = txrr.get_uint32_t();
   uint16_t txIdx  = txrr.get_uint16_t();
   uint16_t outIdx = txrr.get_uint16_t();


   BinaryDataRef txRef(txoData[i].getPtr(), 6);
   bool isFound = seekTo(BLKDATA, DB_PREFIX_BLKDATA, txRef);
   if(!isFound)
   {
      cerr << "***ERROR:  could not find transaction in DB" << endl;
      return false;
   }

   // Need to get the height and hash of the parent transaction
   Tx tx;
   readBlkDataTxValue(currReadValue_, tx)

   // Now get the TxOut directly
   BinaryDataRef rawTxOutRef = getValueRef(BLKDATA, DB_PREFIX_BLKDATA, txoData[i]);
   if(rawTxOutRef.getSize()==0)
   {
      cerr << "***ERROR:  could not find TxOut in DB" << endl;
      return false;
   }

   BinaryRefReader brr(rawTxOutRef);
   TxOut txout;
   readBlkDataTxOutValue(brr, txout);

   utxo.txHash_     = tx.thisHash_;
   utxo.txOutIndex_ = outIdx;
   utxo.txHeight_   = hgtxToHeight(hgtX);
   utxo.value_      = txout.getValue();
   utxo.script_     = txout.getScript();

   return txout.storedIsSpent_;
}

/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::getUtxoListForAddr( BinaryData & const scriptWithType,
                                             vector<UnspentTxOut> & utxoVect)
{
   BinaryWriter bw;
   bw.put_uint8_t(DB_PREFIX_REGADDR);
   bw.put_BinaryData(scriptWithType);

   seekTo(BLKDATA, DB_PREFIX_REGADDR, bw.getData());

   RegisteredAddress ra;
   vector<BinaryData> txoData;

   readRegisteredAddr(ra, &txoData);
   utxoVect.clear();
   utxoVect.reserve(txoData.size());

   for(uint32_t i=0; i<txoData.size(); i++)
   {
      UnspentTxOut utxo;
      bool isSpent = getUnspentTxOut(txoData[i], utxo);
      if(!isSpent)
         utxoVect.push_back(utxo);
   }
   
   return true;

}


bool InterfaceToLevelDB::getFullTxFromKey6B(BinaryData const & key6B)
{

}

bool InterfaceToLevelDB::getFullTxFromHash(BinaryData const & key6B)
{

}


bool InterfaceToLevelDB::readFullTx(Tx & tx, leveldb::Iterator* iter=NULL)
{
   if(iter==NULL)
      iter = iters_[BLKDATA];

   readBlkDataTxKey(currReadKey_, tx);
   if(!tx.isInitialized())
   {
      cerr << "ERROR: iterator is not pointing to a Tx" << endl;
      return false;
   }

   readBlkDataTxValue(currReadValue_, tx);

   if(!tx.isPartial_)
      return;
   
   while(1)
   {
      advanceIterAndRead(iter);
      if(readBlkDataKey5B(currReadKey_) != BLKDATA_TXOUT)
      {
         currReadKey_.resetPosition();
         break;
      }

      TxOut txout;
      readBlkDataTxOutKey(currReadKey_, txout);
      readBlkDataTxOutValue(currReadValue_, txout);

      
   }
}


/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getUtxoHistoryForAddr(BinaryData & const addrScript,
                                               RegisteredAddress & regAddr,
                                               vector<UnspentTxOut> & txoVect=NULL)
{

}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::advanceIterAndRead(leveldb::Iterator* iter)
{
   iter->Next();
   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
}


/////////////////////////////////////////////////////////////////////////////
map<HashString, BlockHeader> InterfaceToLevelDB::getHeaderMap(void)
{
   map<HashString, BlockHeader> outMap;

   leveldb::Iterator* it = dbs_[HEADERS]->NewIterator(leveldb::ReadOptions());
   it->SeekToFirst();
   if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey )
      cerr << "***WARNING: How do we not have a DB info key?" << endl; 
   else
      it->Next()

   BinaryData headerHash;
   BinaryData headerEntry;
   BlockHeader header;
   for (; it->Valid(); it->Next())
   {
      sliceToBinaryData(it->key(),   headerHash);
      sliceToBinaryData(it->value(), headerEntry);

      BinaryRefReader brr(headerEntry);
      header.unserialize(brr);
      uint32_t hgtX    = brr.get_uint32_t();
      uint32_t txCount = brr.get_uint32_t();
      uint32_t nBytes  = brr.get_uint32_t();

      // The "height" is actually a 3-byte height, and a "duplicate ID"
      // Reorgs lead to multiple headers having the same height.  Since 
      // the blockdata
      header.storedHeight_(hgtX >> 8);
      header.duplicateID_(hgtX & 0x000000ff);

      outMap[headerHash] = header;
   }

   return outMap;
}


////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getRawHeader(BinaryData const & headerHash)
{
   // I used the seek method originally to try to return
   // a slice that didn't need to be copied.  But in the 
   // end, I'm doing a copy anyway.  So I switched to 
   // regular DB.Get and commented out the seek method 
   // so it's still here for reference
   static BinaryData headerOut(HEADER_SIZE);
   headerOut = getValue(HEADERS, headerHash);
   return headerOut;
}

////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::addHeader(BinaryData const & headerHash, 
                                   BinaryData const & headerRaw)
{
   static leveldb::Status stat;
   leveldb::Slice key(headerHash.getPtr(), 32);
   leveldb::Slice val(headerRaw.getPtr(), HEADER_SIZE);
   
   stat = db_headers_.Put(leveldb::WriteOptions(), key, val);
   return checkStatus(stat);
}


////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getDBInfoKey(void)
{
   static BinaryData dbinfokey(0);
   if(dbinfokey.getSize() == 0)
   {
      BinaryWriter bw;
      bw.put_uint8_t((uint8_t) DB_PREFIX_DBINFO)
      bw.put_BinaryData( BinaryData(string("DatabaseInfo")));
      dbinfokey = bw.getData();
   }
   return dbinfokey;
}

