#include <iostream>
#include <sstream>
#include "leveldb_wrapper.h"




////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::init()
{
   dbIsOpen_ = false;
   for(uint8_t i=0; i<DB_COUNT; i++)
   {
      iters_[i] = NULL;
      batches_[i] = NULL;
      dbs_[i] = NULL;
      dbPaths_[i] = string("");
   }
}

////////////////////////////////////////////////////////////////////////////////
InterfaceToLevelDB::InterfaceToLevelDB() :
{
   init();
}

////////////////////////////////////////////////////////////////////////////////
// The dbType and pruneType inputs are left blank if you are just going to take 
// whatever is the current state of database.  You can choose to manually 
// specify them, if you want to throw an error if it's not what you were 
// expecting
InterfaceToLevelDB::InterfaceToLevelDB(
                   string             basedir, 
                   BinaryData const & genesisBlkHash, 
                   BinaryData const & genesisTxHash, 
                   BinaryData const & magic,
                   ARMORY_DB_TYPE     dbtype=ARMORY_DB_WHATEVER,
                   DB_PRUNE_TYPE      pruneType=DB_PRUNE_WHATEVER)
{
   init();
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


InterfaceToLevelDB::~InterfaceToLevelDB(void)
{
   for(uint32_t db=0; db<(uint32_t)DB_COUNT; db++)
      if(batchStarts_[db] > 0)
         Log::ERR() << "Shutting down the interface but batch in-progress";

   closeDatabases();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txOutScriptToLDBKey(BinaryData const & script)
{
   BinaryWriter bw(22);  // reserve 21 bytes which is almost always perfect
   bw.put_uint8_t(DB_PREFIX_REGADDR);
   bw.put_BinaryData(getTxOutScriptUniqueKey(script.getRef());
   return bw.getData();
}


/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txHashToLDBKey(BinaryData const & txHash)
{
   // We actually only store the first four bytes of the tx
   BinaryWriter bw(5);
   bw.put_uint8_t(DB_PREFIX_TXHINTS);
   bw.put_BinaryData(txHash, 0, 4);
   return bw.getData();
}



/////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::openDatabases(void)
{
   if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      Log::ERR() << " must set magic bytes and genesis block";
      Log::ERR() << "           before opening databases.";
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
      batchStarts_[db] = 0;
         
      BinaryData dbInfo = getValue(dbs_[db], getDBInfoKey());
      if(dbInfo.getSize() == 0)
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         BitWriter<uint32_t> bitwrite;
         uint32_t flagBytes = 0;
         bitwrite.putBits((uint32_t)ARMORY_DB_VERSION, 4);
         bitwrite.putBits((uint32_t)armoryDbType_,     4);
         bitwrite.putBits((uint32_t)dbPruneType_,      4);

         BinaryWriter bw(48);
         bw.put_uint32_t(ARMORY_DB_VERSION)
         bw.put_BinaryData(magicBytes_);
         bw.put_uint32_t(bitwrite.getValue());
         bw.put_uint32_t(0);
         bw.put_BinaryData(genesisBlkHash_);
   
         putValue(dbs_[db], getDBInfoKey(), bw.getData());
      }
      else
      {
         // Else we read the DB info and make sure everything matches up
         if(dbinfo.getSize() < 40)
         {
            Log::ERR() << "Invalid DatabaseInfo data";
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
            Log::ERR() << " Magic bytes mismatch!  Different blkchain?";
            closeDatabases();
            return false;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValue(dbs_[db], topBlockHash_).getSize() == 0 )
         {
            Log::ERR() << " Top block doesn't exist!";
            closeDatabases();
            return false;
         }

         BitReader<uint32_t> bitread(flags);
         uint32_t dbVer      = bitread.getBits(4);
         uint32_t dbType     = bitread.getBits(4);
         uint32_t pruneType  = bitread.getBits(4);

         if(armoryDbType_ == ARMORY_DB_WHATEVER)
            armoryDbType_ = (ARMORY_DB_TYPE)dbType;
         else if(armoryDbType_ != dbType)
         {
            Log::ERR() << "Mismatch in DB type";
            closeDatabases();
            return false;
         }

         if(dbPruneType_ == DB_PRUNE_WHATEVER)
            dbPruneType_ = (DB_PRUNE_TYPE)pruneType;
         else if(dbPruneType_ != pruneType)
         {
            Log::ERR() << "Mismatch in DB type";
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

   dbIsOpen_ = true;
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
void InterfaceToLevelDB::startBatch(DB_SELECT db)
{
   if(batchStarts_[db] == 0)
   {
      if(batches_[db] != NULL)
      {
         Log::ERR() << "Trying to startBatch but we already have one";
         delete batches_[db];
      }

      batches_[db] = new WriteBatch;
   }

   // Increment the number of times we've called this function
   batchStarts_[db] += 1;
}



////////////////////////////////////////////////////////////////////////////////
// Commit all the batched operations
void InterfaceToLevelDB::commitBatch(DB_SELECT db)
{
   // Decrement the numbers of starts and only write if it's at zero
   batchStarts_[db] -= 1;

   if(batchStarts_[db] == 0)
   {
      if(batches_[db] == NULL)
      {
         Log::ERR() << "Trying to commitBatch but we don't have one";
         return;
      }

      dbs_[db]->Write(leveldb::WriteOptions(), batches_[db]);
      delete batches_[db];
      batches_[db] = NULL;
   }
}

////////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
void InterfaceToLevelDB::commitBatch(DB_SELECT db, doSync=false)
{
   if(batches_[db] == NULL)
   {
      Log::ERR() << " Can't commit NULL WriteBatch";
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
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, BinaryDataRef key)
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
                                        BinaryDataRef key)
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
BinaryDataRef InterfaceToLevelDB::getValueRef(DB_SELECT db, BinaryDataRef key)
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
                                              BinaryDataRef key)
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
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
   leveldb::Slice ldbVal((char*)value.getPtr(), value.getSize());
   
   if(batches_[db]!=NULL)
      batches_[db]->Put(ldbkey, &value);
   else
   {
      leveldb::Status stat = dbs_[db]->Put(leveldb::WriteOptions(), ldbkey, &value);
      checkStatus(stat);
   }
}

/////////////////////////////////////////////////////////////////////////////
// Put value based on BinaryData key.  If batch writing, pass in the batch
void InterfaceToLevelDB::putValue(DB_SELECT db, 
                                  DB_PREFIX prefix,
                                  BinaryDataRef key, 
                                  BinaryDataRef value)
{
   BinaryWriter bw;
   bw.put_uint8_t((uint8_t)prefix);
   bw.put_BinaryData(key);
   putValue(db, bw.getDataRef(), value);
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
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         bool withPrefix)
{
   BinaryWriter bw(5);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         uint16_t txIdx, 
                         bool withPrefix)
{
   BinaryWriter bw(7);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(txIdx);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
inline BinaryData InterfaceToLevelDB::getBlkDataKey(
                         uint32_t height, 
                         uint8_t  dup,
                         uint16_t txIdx,
                         uint16_t txOutIdx,
                         bool withPrefix)
{
   BinaryWriter bw(9);
   if(withPrefix)
      bw.put_uint8_t(DB_PREFIX_BLKDATA);
   bw.put_uint32_t(heightAndDupToHgtx(height,dup));
   bw.put_uint16_t(txIdx);
   bw.put_uint16_t(txOutIdx);
   return bw.getData();
}


/////////////////////////////////////////////////////////////////////////////
// Not sure why this is useful over getHeaderMap() ... this iterates over
// the headers in hash-ID-order, instead of height-order
void InterfaceToLevelDB::startHeaderIteration()
{
   seekTo(HEADERS, DB_PREFIX_HEADHASH, BinaryData(0));
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::startBlockIteration(void)
{
   char prefix = DB_PREFIX_BLKDATA;
   seekTo(BLKDATA, DB_PREFIX_BLKDATA, BinaryData(0));
   leveldb::Slice start(&prefix, 1);
   iters_[BLKDATA]->Seek(start);
   iteratorToRefReaders(iters_[BLKDATA], currReadKey_, currReadValue_);
}


/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLevelDB::advanceToNextBlock(bool skip)
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
   Log::ERR() << "we should never get here...";
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
                                BinaryData const & key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   it.Seek(binaryDataToSlice(key));
   if(!it->Valid())
      return false;

   iteratorToRefReaders(it, currReadKey_, currReadValue_);
   uint32_t sz = currReadKey_.getSize();
   bool isMatch = (currReadKey_.get_BinaryDataRef(sz)==key);
   currReadKey_.resetPosition();
   return isMatch;
}

/////////////////////////////////////////////////////////////////////////////
// If we are seeking into the HEADERS DB, then ignore prefix
bool InterfaceToLevelDB::seekTo(DB_SELECT db,
                                DB_PREFIX prefix, 
                                BinaryData const & key,
                                leveldb::Iterator* it)
{
   if(it==NULL)
      it = iters_[db];

   BinaryData ldbkey;
   if(db==HEADERS)
      return seekTo(db, key, it);
   else
   {
      uint8_t prefInt = (uint8_t)prefix;
      ldbkey = BinaryData(&prefInt, 1) + key;
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
      Log::ERR() << "Tried to getBlock() but none left";
      return;
   }

    
   // Read the key for the block
   BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                          bh.blockHeight_,
                                          bh.duplicateID_);

   if(bdtype == NOT_BLKDATA)
   {
      Log::ERR() << "somehow did not advance to new;
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
         Log::ERR() << "Invalid index for tx at height " << (hgtX>>8)
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
   // Unserialize the raw header into the SBH object
   bh.unserialize(brr);

   // Read the flags byte
   BitReader<uint32_t> bitr32(brr.get_uint32_t());

   uint32_t        dbVersion  =                  bitr32.getBits(4);
   uint32_t        blkVersion =                  bitr32.getBits(4);
   ARMORY_DB_TYPE  dbtype     = (ARMORY_DB_TYPE) bitr32.getBits(4);
   DB_PRUNE_TYPE   pruneType  = (DB_PRUNE_TYPE)  bitr32.getBits(2);
   MERKLE_SER_TYPE merkType   = (MERKLE_SER_TYPE)bitr32.getBits(2);

   bh.storedNumTx_    = brr.get_uint32_t();
   bh.storedNumBytes_ = brr.get_uint32_t();

   if(dbVersion != (uint8_t)ARMORY_DB_VERSION)
   {
      Log::ERR() << "Version mismatch in IFTLDB::getBlock()";
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
      Log::ERR() << "Unexpected bytes remaining: " << brr.getSizeRemaining();
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
   // flags
   //    DBVersion      4 bits
   //    TxVersion      2 bits
   //    isValid        2 bits   (Unknown,  Valid, NotValid)
   //    HowTxSer       4 bits   (FullTxOut, TxNoTxOuts, numTxOutOnly)
   BitReader<uint16_t> bitread(brr); // flags
   uint16_t dbVer   = bitread.getBits(4);
   uint16_t txVer   = bitread.getBits(2);
   uint16_t isValid = bitread.getBits(2);
   uint16_t txSer   = bitread.getBits(4);
   
   brr.get_BinaryData(tx.thisHash_, 32);

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
   // Similar to TxValue flags
   //    DBVersion   4 bits
   //    TxVersion   2 bits
   //    isValid     2 bits
   //    Spentness   2 bits
   BitReader<uint16_t> bitread(brr);
   uint16_t dbVer   =  bitread.getBits(4);
   uint16_t txVer   =  bitread.getBits(2);
   uint16_t isValid =  bitread.getBits(2);
   uint16_t isSpent =  bitread.getBits(2);
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
      Log::ERR() << "Tried to access invalid iterator!";
      return;
   }

   iteratorToRefReaders(iter, currReadKey_, currReadValue_);
    
   if( currReadKey_.get_uint8_t() != (uint8_t)DB_PREFIX_REGADDR)
   { 
      Log::ERR() << "Iterator does not point to a registered address";
      return;
   }
      
   uint32_t nBytes = currReadKey_.getSizeRemaining();
   regAddr.addrType_ = currReadKey_.get_uint8_t()
   currReadKey_.get_BinaryData(regAddr.uniqueKey_, nBytes);

   // Now read the stored data fro this registered address
   BitReader<uint16_t> bitread(currReadValue_);
   uint8_t version               =                     bitread.getBits(4);
   DB_PRUNE_TYPE pruneType       = (DB_PRUNE_TYPE)     bitread.getBits(2);
   REGADDR_UTXO_TYPE txoListType = (REGADDR_UTXO_TYPE) bitread.getBits(2);
   



   regAddr.alreadyScannedUpToBlk_ = currReadValue_.get_uint32_t();
   regAddr.sumValue_ = currReadValue_.get_uint64_t();

    

   if(txoListType == REGADDR_UTXO_TREE)
   {
      Log::ERR() << " TXO-trees are not implemented, yet!";
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
      Log::ERR() << " could not find transaction in DB";
      return false;
   }

   // Need to get the height and hash of the parent transaction
   Tx tx;
   readBlkDataTxValue(currReadValue_, tx)

   // Now get the TxOut directly
   BinaryDataRef rawTxOutRef = getValueRef(BLKDATA, DB_PREFIX_BLKDATA, txoData[i]);
   if(rawTxOutRef.getSize()==0)
   {
      Log::ERR() << " could not find TxOut in DB";
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
   BinaryWriter bw(22);
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



bool InterfaceToLevelDB::readFullTx(Tx & tx, leveldb::Iterator* iter=NULL)
{
   if(iter==NULL)
      iter = iters_[BLKDATA];

   readBlkDataTxKey(currReadKey_, tx);
   if(!tx.isInitialized())
   {
      Log::ERR() << "iterator is not pointing to a Tx";
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

   iters_[HEADERS]->SeekToFirst();
   if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey() )
      Log::WARN() << "How do we not have a DB info key?" ;
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
      header.storedHeight_(hgtxToHeight(hgtX));
      header.duplicateID_(hgtxToDupID(hgtX));

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
   headerOut = getValue(HEADERS, DB_PREFIX_HEADHASH, headerHash);
   return headerOut;
}



////////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::getDBInfoKey(void)
{
   // Return a key that is guaranteed to be before all other non-empty
   // DB keys
   static BinaryData dbinfokey(0);
   if(dbinfokey.getSize() == 0)
   {
      BinaryWriter bw(1);
      bw.put_uint8_t((uint8_t)DB_PREFIX_DBINFO); 
      dbinfokey = bw.getData();
   }
   return dbinfokey;
}

StoredTx InterfaceToLevelDB::getFullTxFromKey6B(BinaryDataRef key6B)
{

}

StoredTx InterfaceToLevelDB::getFullTxFromHash(BinaryDataRef txHash)
{

}


////////////////////////////////////////////////////////////////////////////////
/*  I think the BDM will do this, not the DB interface
bool InterfaceToLevelDB::addBlockToDB(BinaryDataRef newBlock,
                                      bool withLead8B, 
                                      UPDATE_DB_TYPE updType=UPDATE_DB_NORMAL)
{
   
   BinaryRefReader brr(newBlock);

   if(withLead8B)
   {
      BinaryDataRef first4 = brr.get_BinaryDataRef(4);
      if(first4 != magicBytes_)
      {
         Log::ERR() << "Magic bytes don't match! " << first4.toHexStr().c_str();
         return false;
      }
      
      // The next 4 bytes is the block size, but we will end up computing this
      // anyway, as we dissect the block.
      brr.advance(4);
   }

   BlockHeader bh(brr);
   
   uint32_t nTx = brr.get_var_int();
   vector<Tx> allTxInBlock(nTx);
   for(uint32_t itx=0; itx<nTx; itx++)
      allTxInBlock[itx].unserialize(brr);
   
   
   // Check whether the DB has it already.
   bool chkAlready = (getValue(HEADERS, bh.getThisHash()).getSize() == 0);

   bool doValid;
   bool skipEntirely = false;
   if(updType==UPDATE_DB_NORMAL)
   {
   }
   
}
*/



////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  
void InterfaceToLevelDB::serializeStoredBlockHeaderValue(
                                          DB_SELECT db,
                                          StoredBlockHeader const & sbh,
                                          BinaryWriter & bw)
{
   if(!sbh.isInitialized_)
   {
      Log::ERROR() << "Attempted to serialize uninitialized block header";
      return;
   }

   if(db==HEADERS)
   {
      uint32_t hgtx = heightAndDupToHgtx(sbh.blockheight, sbh.duplicateID_);
      bw.put_BinaryData(sbh.dataCopy_);
      bw.put_uint32_t(hgtx);
   }
   else if(db==BLKDATA)
   {
      uint32_t version = *(uint32_t*)sbh.dataCopy_.getPtr();

      MERKLE_SER_TYPE mtype;
      switch(armoryDbType_)
      {
         // If we store all the tx anyway, don't need any/partial merkle trees
         case ARMORY_DB_LITE:    mtype = MERKLE_SER_PARTIAL; break;
         case ARMORY_DB_PARTIAL: mtype = MERKLE_SER_FULL;    break;
         case ARMORY_DB_FULL:    mtype = MERKLE_SER_NONE;    break;
         case ARMORY_DB_SUPER:   mtype = MERKLE_SER_NONE;    break;
         default: 
            Log::ERR() << "Invalid DB mode in serializeStoredBlockHeaderValue";
      }
      
      if(sbh.merkle_.getSize() > 0)
         mtype = (sbh.merkleIsPartial_ ? MERKLE_SER_PARTIAL : MERKLE_SER_FULL);
   
      // Create the flags byte
      BitWriter<uint32_t> bitwrite;
      bitwrite.putBits((uint32_t)ARMORY_DB_VERSION,  4);
      bitwrite.putBits((uint32_t)version,            4);
      bitwrite.putBits((uint32_t)armoryDbType_,      4);
      bitwrite.putBits((uint32_t)dbPruneType_,       2);
      bitwrite.putBits((uint32_t)mtype,              2);
      uint32_t flags = bitwrite.getValue();

      bw.put_uint32_t(flags);
      bw.put_BinaryData(sbh.dataCopy_);
      bw.put_uint32_t(sbh.numTx_);
      bw.put_uint32_t(sbh.numBytes_);

      if( mtype != MERKLE_SER_NONE )
         bw.put_BinaryData(sbh.merkle_);
   }
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::serializeStoredTxValue(
                                          StoredTx const & stx,
                                          BinaryWriter & bw)
{
   uint32_t version = *(uint32_t*)stx.dataCopy_.getPtr();
   uint32_t validity = (stx.isValid_ ? 1 : 0);
   
   switch(armoryDbType_)
   {
      // If we store all the tx anyway, don't need any/partial merkle trees
      case ARMORY_DB_LITE:    mtype = TX_SER_FRAGGED; break;
      case ARMORY_DB_PARTIAL: mtype = TX_SER_FRAGGED; break;
      case ARMORY_DB_FULL:    mtype = TX_SER_FULL;    break;
      case ARMORY_DB_SUPER:   mtype = TX_SER_FULL;    break;
      default: 
         Log::ERR() << "Invalid DB mode in serializeStoredTxValue";
   }

   BitWriter<uint16_t> bitwrite;
   bitwrite.putBits((uint16_t)ARMORY_DB_VERSION,  4);
   bitwrite.putBits((uint16_t)version,            4);
   bitwrite.putBits((uint16_t)validity,           2);
   bitwrite.putBits((uint16_t)txSerType,          2);

   
   bw.put_uint32_t(bitwrite.getValue());
   bw.put_BinaryData(stx.thisHash_);

   if(txSerType == TX_SER_FULL    || 
      txSerType == TX_SER_FRAGGED )
      bw.put_BinaryData(stx.dataCopy_);
   else:
      bw.put_var_int(stx.numTxOut_);
}


////////////////////////////////////////////////////////////////////////////////
// We assume that the SBH has the correct blockheight already included.  Will 
// adjust the dupID value  in the input SBH
// Will overwrite existing data, for simplicity, and so that this method allows
// us to easily replace/update data, even if overwriting isn't always necessary
void InterfaceToLevelDB::putStoredBlockHeader(
                          StoredBlockHeader & sbh,
                          bool withTx)
{
   uint32_t height  = sbh.blockHeight_;
   bool     isValid = sbh.isMainBranch_;

   // First, check if it's already in the hash-indexed DB
   BinaryData existingHead = getValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_);
   if(existingHead.getSize() > 0)
   {
      // Felt like there was something else to do here besides Log::WARN...
      Log::WARN() << "Header already exists in DB.  Overwriting";
   }

   // Check if it's already in the height-indexed DB - determine dupID if not
   bool alreadyInHgtDB = false;
   BinaryData hgt4((uint8_t*)&height, 4);
   BinaryData hgtList = getValue(HEADERS, DB_PREFIX_HEADHGT, hgt4);
   if(hgtList.getSize() == 0)
      sbh.setParamsTrickle(height, 0, isValid);
   else
   {
      int const lenEntry = 17;
      if(hgtList.getSize() % lenEntry > 0)
         Log::ERR() << "Invalid entry in headers-by-hgt db";

      int8_t maxDup = -1;
      for(uint8_t i=0; i<hgtList.getSize() / lenEntry; i++)
      {
         uint8_t dupID =  *(hgtList.getPtr() + i*lenEntry) & 0x7f;
         bool    valid = (*(hgtList.getPtr() + i*lenEntry) & 0x80) > 0;
         maxDup = max(maxDup, (int8_t)dupID);
         BinaryDataRef hash16 = hgtList.getSliceRef(lenEntry*i+1, lenEntry-1);
         if(sbh.thisHash_.startsWith(hash16))
         {
            alreadyInHgtDB = true;
            sbh.setParamsTrickle(height, i, isValid);
         }
      }

      if(!alreadyInHgtDB)
         sbh.setParamsTrickle(height, maxDup+1, isValid);
   }
   
   startBatch(HEADERS);

   if(!alreadyInHgtDB)
   {
      // Top bit is "isMainBranch_", lower 7 is the dupID
      uint8_t dup8 = sbh.duplicateID_ | (sbh.isMainBranch_ ? 0x80 : 0x00);

      // Make sure it exists in height index.  Put the new ones first so 
      // we can do less searching (since the last one stored is almost 
      // always the one we think is valid
      BinaryWriter bw;
      bw.put_uint8_t(dup8);
      bw.put_BinaryData(sbh.thisHash_.getSliceRef(0,16));
      bw.put_BinaryData(hgtList);
      putValue(HEADERS, DB_PREFIX_HEADHGT, hgt4, bw.getDataRef());
   }
      
   // Overwrite the existing hash-indexed entry, just in case the dupID was
   // not known when previously written.  
   BinaryWriter bwHeaders;
   serializeStoredBlockHeader(HEADERS, sbh, bwHeaders);
   putValue(HEADERS, DB_PREFIX_HEADHASH, sbh.thisHash_, bwHeaders.getDataRef());

   commitBatch(HEADERS);


   // For blkdata
   if(withTx)
      startBatch(BLKDATA);

   // Now put the data into the blkdata DB
   BinaryData key = getBlkDataKey(sbh.blockHeight_, sbh.duplicateID_);
   BinaryWriter bwBlkData;
   serializeStoredBlockHeader(BLKDATA, sbh, bwBlkData);
   putValue(BLKDATA, DB_PREFIX_BLKDATA, key.getRef(), bwBlkData.getDataRef());
   
   // If we only wanted to update the BlockHeader record, we're done.
   if(!withTx)
      return;
   
   for(uint32_t i=0; i<numTx_; i++)
   {
      map<uint32_t, StoredTx>::iterator txIter = txMap_.find(i);
      if(txIter != txMap_.end())
      {
         // Make sure the txIndex value is correct, then dump it to DB.
         txIter->second.txIndex_ = i;

         // When writing out the tx, we always write out the TxOuts.  
         // (that's what the second "true" argument is specifying)
         // There's no situation where we indicate *at the block-header 
         // level*, that we want to put the Txs but not the TxOuts.  
         // In other contexts, it may be desired to put/update a Tx 
         // without updating the TxOuts.
         putStoredTx(txIter->second, true);
      }
   }

   commitBatch(BLKDATA);
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getStoredBlockHeader(
                          StoredBlockHeader & sbh,
                          BinaryDataRef headHash, 
                          bool withTx)
{

}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getStoredBlockHeader(
                          StoredBlockHeader & sbh,
                          uint32_t blockHgt,
                          uint8_t blockDup,
                          bool withTx)
{

}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::putStoredTx(         
                          StoredTx const & stx,
                          bool withTxOut)
{
   BinaryData ldbKey = getBlkDataKey(stx.blockHeight_, 
                                     stx.blockDupID_, 
                                     stx.txIndex_,
                                     false);

   startBatch(BLKDATA);

   // First, check if it's already in the hash-indexed DB
   BinaryData hash4(stx.thisHash_.getSliceRef(0,4));
   BinaryData existingHints = getValue(BLKDATA, DB_PREFIX_HINT, hash4);

   // We need to add a txhint
   if(existingHints.getSize() > 0)
   {
      uint32_t numHints = existingHints.getSize() / 6;
      bool alreadyHasHint = false;
      for(uint32_t i=0; i<numHints; i++)
      {
         if(existingHints.getSliceRef(i*6, 6) == ldbKey)
         {
            alreadyHasHint = true;
            break;
         }
      }
      
      if(!alreadyHasHint)
      {
         BinaryWriter bw;
         bw.put_BinaryData(ldbKey);
         bw.put_BinaryData(existingHints);
         putValue(BLKDATA, DB_PREFIX_TXHINTS, hash4, bw.getDataRef());
      }
         
   }


   BinaryWriter bw;
   serializeStoredTxValue(stx, bw);
   putValue(BLKDATA, DB_PREFIX_BLKDATA, ldbKey, bw.getDataRef());

   if(withTxOut)
   {
      map<uint32_t, StoredTxOut>::iterator iter;
      for(iter  = txOutMap_.begin();
         iter != txOutMap_.end();
         iter++)
      {
         // Put all o
         putStoredTxOut(iter->second);
      }
   }

   commitBatch(BLKDATA);
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getStoredTx(         
                          StoredTx & st,
                          BinaryDataRef txHash, 
                          bool withTxOut)
{

}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::putStoredTxOut(      
                          StoredTxOut const & stxo)
{

}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getStoredTxOut(      
                          StoredTxOut & sto,
                          BinaryDataRef txHash)
{

}



////////////////////////////////////////////////////////////////////////////////
bool InterfaceToLevelDB::updateHeaderHeight(BinaryDataRef headHash, 
                                            uint32_t height, uint8_t dup)
{
   BinaryDataRef headVal = getValueRef(HEADERS, headHash);
   if(headVal.isNull())
   {
      Log::ERR() << " Attempted to update a non-existent header!";
      return false;
   }
      
   BinaryWriter bw(HEADER_SIZE + 4);
   bw.put_BinaryData(headVal.getPtr(), HEADER_SIZE);
   bw.put_uint32_t(heightAndDupToHgtx(height, dup));

   putValue(HEADERS, headHash, bw.getDataRef());
   return true;
}  

