#include <iostream>
#include <sstream>
#include "leveldb_wrapper.h"


InterfaceToLevelDB::InterfaceToLevelDB(
                   string basedir, 
                   BinaryData const & genesisBlkHash,
                   BinaryData const & genesisTxHash,
                   BinaryData const & magic,
                   ARMORY_DB_TYPE     dbtype=ARMORY_DB_DEFAULT,
                   DB_PRUNE_TYPE      pruneType=DB_PRUNE_NONE)
{
   baseDir_ = basedir;
   char dbname[1024];

   stringstream head;
   head << baseDir_ << "/" << "leveldb_headers"
   dbPaths_[0] = head.str()

   stringstream blk;
   blk << baseDir_ << "/" << "leveldb_blkdata"
   dbPaths_[1] = blk.str()
   
   magicBytes_ = magic;
   genesisTxHash_ = genesisTxHash
   genesisBlkHash_ = genesisBlkHash;

   // Open databases and check that everything is correct
   // Or create the databases and start it up
   openDatabases();

}

BinaryData InterfaceToLevelDB::txOutScriptToLevelDBKey(BinaryData const & script)
{
   BinaryWriter bw;
   bw.put_uint8_t(BLK_PREFIX_REGADDR)
   bw.put_var_int(script.getSize()) 
   bw.put_BinaryData(script.getRef());
   return bw.getData();
}



/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::headerHashToLevelDBKey(BinaryData const & headHash)
{
   BinaryWriter bw;
   bw.put_uint8_t(BLK_PREFIX_HEADERS);
   bw.put_BinaryData(headHash);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
BinaryData InterfaceToLevelDB::txHashToLevelDBKey(BinaryData const & txHash)
{
   // We actually only store the first four bytes of the tx
   BinaryWriter bw;
   bw.put_uint8_t(BLK_PREFIX_BLKDATA);
   bw.put_BinaryData(txHash, 0, 4);
   return bw.getData();
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::openDatabases(void)
{
   if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
   {
      cerr << "***ERROR:  must set magic bytes and genesis block!" << endl;
      return;
   }

   leveldb::Status stat;
   leveldb::Options opts1;
   opts1.create_if_missing  = true;
   //opts1.compression        = leveldb::kNoCompression;
   //opts1.filter_policy      = leveldb::NewBloomFilter(10);
   checkStatus(leveldb::DB::Open(opts1, headPath_,  &db_headers_));


   leveldb::Options opts2;
   opts2.create_if_missing  = true;
   //opts2.compression        = leveldb::kNoCompression;
   //opts2.filter_policy      = leveldb::NewBloomFilter(10);
   checkStatus(leveldb::DB::Open(opts2, dbname,  &db_blkdata_));

   vector<leveldb::DB*> dbs[2];
   for(uint32_t db=0; db<DB_COUNT; db++)
   {
      leveldb::Options opts;
      opts.create_if_missing = true;
      //opts2.compression        = leveldb::kNoCompression;
      //opts2.filter_policy      = leveldb::NewBloomFilter(10);
      checkStatus(leveldb::DB::Open(opts2, dbPaths_[db],  &dbs_[db]));
         
      BinaryData dbInfo = getValue(dbs_[db], getDBInfoKey());
      if(dbInfo.getSize() == 0)
      {
         // If DB didn't exist yet (dbinfo key is empty), seed it
         // A new database has the maximum flag settings
         // Flags can only be reduced.  Increasing requires redownloading
         uint32_t flagBytes = 0;
         flagBytes |= ARMORY_DB_VERSION << 28;
         flagBytes |= (uint32_t)ARMORY_DB_SUPER << 24;
         flagBytes |= (uint32_t)DB_PRUNE_NONE << 20;

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
            return;
         }
         BinaryReader br(dbinfo);
         uint32_t version = br.get_uint32_t();
         BinaryData magic = br.get_BinaryData(4);
         BinaryData flags = br.get_BinaryData(4);
         topBlockHeight_  = br.get_uint32_t();
         topBlockHash_    = br.get_BinaryData(32);
      
         // Check that the magic bytes are correct
         if(magicBytes_ != magic)
         {
            cerr << "***ERROR:  Magic bytes mismatch!  Different blkchain?" << endl;
            closeDatabases();
            return;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValue(dbs_[db], topBlockHash_).getSize() == 0 )
         {
            cerr << "***ERROR:  Top block doesn't exist!" << endl;
            closeDatabases();
            return;
         }
         
      }
      
   }

}



/////////////////////////////////////////////////////////////////////////////
// DBs don't really need to be closed.  Just delete them
void InterfaceToLevelDB::closeDatabases(void)
{
   for(uint32_t db=0; db<DB_COUNT; db++)
      delete dbs_[db];
}


/////////////////////////////////////////////////////////////////////////////
// Get value using pre-created slice
BinaryData InterfaceToLevelDB::getValue(DB_SELECT db, leveldb::Slice ldbKey)
{
   string value;
   leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbKey, &value);
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
   char prefix = BLK_PREFIX_BLKDATA;
   leveldb::Slice start(&prefix, 1);
   iterBlkData_ = db_blkdata_->NewIterator(leveldb::ReadOptions());
   iterBlkData_->Seek(start);
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::getNextBlock(void)
{
   while
   iterHeaders_->Next()
}

/////////////////////////////////////////////////////////////////////////////
// "Skip" refers to the behavior that the previous operation may have left
// the iterator already on the next desired block.  So our "advance" op may
// have finished before it started.  Alternatively, we may be on this block 
// because we checked it and decide we don't care, so we want to skip it.
bool InterfaceToLevelDB::advanceToNextBlock(bool skip=false)
{
   char prefix = BLK_PREFIX_BLKDATA;

   leveldb::Iterator* it = iters_[BLKDATA];
   BinaryData key;
   while(1) 
   {
      if(skip) it->Next();

      if( !it->Valid() || it->key()[0] != (char)BLK_PREFIX_BLKDATA)
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
void InterfaceToLevelDB::getBlock( BlockHeader & bh, 
                                   vector<Tx> & txList,         
                                   leveldb::Iterator* iter=NULL,
                                   ignoreMerkle = true)
{
   bool isAnotherBlock = advanceToNextBlock();
   if(!isAnotherBlock)
   {
      cerr << "Tried to getBlock() but none left" << endl;
      return;
   }

   // If an iterator was passed in, switch to the data there, but restore
   // the class members later, afterwards.
   bool customIter = (iter != NULL);
   BinaryRefReader prevReaderKey = currReadKey_;
   BinaryRefReader prevReaderVal = currReadValue_;
   if(customIter)
      iteratorToRefReaders(iter, currReadKey_, currReadValue_);

    
   // Read the key for the block
   BLKDATA_TYPE bdtype = readBlkDataKey5B(currReadKey_,
                                          bh.storedHeight_,
                                          bh.duplicateID_);

   if(bdtype == NOT_BLKDATA)
   {
      cerr << "***ERROR: somehow did not advance to new block)";
      return; 
   }

   
   // Read the header and the extra data with it.
   readBlkDataHeaderValue(currReadValue_, bh, ignoreMerkle);
   

   txList.resize(numTx);
   vector<bool> didHitTx(numTx)
   vector<bool> didHitTx(numTx)
   for(uint32_t tx=0; tx<numTx; tx++)
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
         readBlkDataTxValue(currReadValue_, txList[currTxIndex])

      if(bdtype == BLKDATA_TXOUT)
      {
         currTxOutIndex = currReadKey_.get_uint16_t(); 
         readBlkDataTxOutValue(currReadValue_, txList[currTxIndex], currTxOutIndex);
      }

   }

   if(customIter)
   {
      currReadKey_   = prevReaderKey;
      currReadValue_ = prevReaderVal;
   }

}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataHeaderValue( 
                                 BinaryRefReader & brr,
                                 BlockHeader & bh,
                                 bool ignoreMerkle)
{
   uint32_t flags = brr.get_uint32_t();
   bh.unserialize(brr);
   bh.storedNumTx_    = brr.get_uint32_t();
   bh.storedNumBytes_ = brr.get_uint32_t();


   uint32_t version            = (flags & 0xf0000000) >> 28;
   ARMORY_DB_TYPE dbtype       = (flags & 0x0f000000) >> 24;
   DB_PRUNE_TYPE prntype       = (flags & 0x00f00000) >> 20;
   MERKLE_SER_TYPE merkleCode  = (flags & 0x000c0000) >> 18;

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
   if(prefix != BLK_PREFIX_BLKDATA)
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
void InterfaceToLevelDB::readBlkDataTxKey( BinaryRefReader & brr, Tx & tx)
{
   BLKDATA_TYPE bdtype = readBlkDataKey5B(brr, tx.storedHeight_, tx.storedDupID_);
   if(bdtype != BLK_PREFIX_BLKDATA)
      return

   tx.storedIndex_ = brr.get_uint16_t()
}

////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr, Tx & tx)
{
   BLKDATA_TYPE bdt = readBlkDataKey5B(brr, tx.storedHeight_, tx.storedDupID_);
   if(bdt != BLK_PREFIX_BLKDATA)
      return

   tx.storedIndex_ = brr.get_uint16_t()
   tx = brr.get_uint16_t()
}

////////////////////////////////////////////////////////////////////////////////
TxOut InterfaceToLevelDB::readBlkDataTxOutKey( BinaryRefReader & brr)
{
   TxOut txo;
   BLKDATA_TYPE bdt = readBlkDataKey5B(brr, txo.storedHeight_, txo.storedDupID_);
   if(bdt != BLK_PREFIX_BLKDATA)
      return

   txo.storedTxIndex_ = brr.get_uint16_t()
   txo.index_ = brr.get_uint16_t()
}


////////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxValue( BinaryRefReader & brr, Tx& tx)
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
   
   if(txSer == TX_SER_FULL || txSer == TX_SER_NOTXOUT)
      tx.unserialize(brr);
   else
      tx->storedNumTxOut_ = brr.get_var_int();

   tx->version_ = (uint32_t)txVer;
   tx->storedValid_ = isValid;
}

/////////////////////////////////////////////////////////////////////////////
void InterfaceToLevelDB::readBlkDataTxOutValue(BinaryRefReader & brr, TxOut& txOut)
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
   static leveldb::Status stat;
   static BinaryData headerOut(HEADER_SIZE);
   static BinaryData nullHeader(0);
   
   static string headerVal;
   leveldb::Slice key(headerHash.getPtr(), 32);
   stat = db_headers_.Get(leveldb::ReadOptions(), key, &headerVal);
   if(checkStatus(stat))
      return headerOut;
   else
      return nullHeader;
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
   // Make the 20-bytes of zeros followed by "DatabaseInfo".  We
   // do this to make sure it's always at the beginning of an iterator
   // loop and we can just skip the first entry, instead of checking
   // each key in the loop
   static BinaryData dbinfokey(0);
   if(dbinfokey.getSize() == 0)
   {
      BinaryWriter bw;
      bw.put_uint8_t((uint8_t) BLK_PREFIX_DBINFO)
      bw.put_BinaryData( BinaryData(string("DatabaseInfo")));
      dbinfokey = bw.getData();
   }
   return dbinfokey;
}

