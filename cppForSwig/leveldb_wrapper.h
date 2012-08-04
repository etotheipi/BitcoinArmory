#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
//
////////////////////////////////////////////////////////////////////////////////

class BlockDataManager_LevelDB
{



private:
   string baseDir_;
   
   leveldb::DB* db_rawheaders_;  // HeaderHash (32B) --> RawHeader (80B)
   leveldb::DB* db_merklelist_;  // HeaderHash (32B) --> vector<TxHash> (Nx32B)
   leveldb::DB* db_rawtxstore_;  // TxHash     (32B) --> RawTx
   leveldb::DB* db_txmappings_;  // TxHash     (32B) --> HeaderHash,TxIndex
   leveldb::DB* db_walletdata_;  // Hash160    (32B) --> TxOuts (full or unspent)

   void openDatabases(void)
   {
      leveldb::Options opts;
      opts.create_if_missing  = true;
      opts.compression        = leveldb::kNoCompression;
      //opts.filter_policy      = leveldb::NewBloomFilter(10);

      char dbname[1024];
      leveldb::Status stat;
      
      sprintf(dbname, "%s/leveldb_rawheaders", baseDir_);
      checkStatus(leveldb::DB::Open(opts, dbname,  &db_rawheaders_));
      
      sprintf(dirname, "%s/leveldb_merklelist", baseDir_);
      checkStatus(leveldb::DB::Open(opts, dbname,  &db_merklelist_));

      sprintf(dirname, "%s/leveldb_rawtxstore", baseDir_);
      checkStatus(leveldb::DB::Open(opts, dbname,  &db_rawtxstore_));

      sprintf(dirname, "%s/leveldb_txmappings", baseDir_);
      checkStatus(leveldb::DB::Open(opts, dbname,  &db_txmappings_));

      sprintf(dirname, "%s/leveldb_walletdata", baseDir_);
      checkStatus(leveldb::DB::Open(opts, dbname,  &db_walletdata_));
   }


   BinaryData getRawHeader(BinaryData const & headerHash)
   {
      // I used the seek method originally to try to return
      // a slice that didn't need to be copied.  But in the 
      // end, I'm doing a copy anyway.  So I switched to 
      // regular DB.Get and commented out the seek method 
      // so it's still here for reference
      static leveldb::Status stat;
      static BinaryData headerOut(HEADER_SIZE);
      static BinaryData nullHeader(0);
      //static leveldb::Iterator* ldbiter = 
                 //db_rawheaders_.NewIterator(leveldb::ReadOptions());

      //leveldb::Slice key(headerHash.getPtr(), 32);
      //ldbiter.Seek(key);
      //headerOut.copyFrom(ldbiter->value().data(), HEADER_SIZE);
      //if(ldbiter->Valid() && 
         //strcmp(ldbiter->key().data(), headerHash,getPtr(), 32)==0)
         //return headerOut;
      //else:
         //return nullHeader;
      
      static string headerVal;
      leveldb::Slice key(headerHash.getPtr(), 32);
      stat = db_rawheaders_.Get(leveldb::ReadOptions(), key, &headerVal);
      if(checkStatus(stat))
         return headerOut;
      else
         return nullHeader;
   }

   bool addHeader(BinaryData const & headerHash, 
                  BinaryData const & headerRaw)
   {
      static leveldb::Status stat;
      leveldb::Slice key(headerHash.getPtr(), 32);
      leveldb::Slice val(headerRaw.getPtr(), HEADER_SIZE);
      
      stat = db_rawheaders_.Put(leveldb::WriteOptions(), key, val);
      return checkStatus(stat);
   }

   bool checkStatus(leveldb::Status stat)
   {
      if( stat.ok() )
         return true;
   
      cout << "***LevelDB Error: " << stat.ToString() << endl;
      return false;
   }
};


#endif
