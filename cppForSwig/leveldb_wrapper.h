#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"
#include "BtcUtils.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
//
////////////////////////////////////////////////////////////////////////////////

#define TX_VERSION    0x01
#define HEADER_QUAD   0x00
#define TX_LIST_QUAD  0x20
#define ADDR_QUAD     0x20

class InterfaceToLevelDB
{

   BinaryData txOutScriptToLevelDBKey(BinaryData const & script)
   {
      // Put the 0xa0 for ADDR:  it's really just a TxOut script
      BinaryWriter bw;
      bw.put_uint8_t(0xa0 | 0x01);
      bw.put_var_int(script.getSize()) 
      bw.put_BinaryData(script.getRef());
      return bw.getData();
   }



   void openDatabases(void)
   {
      //opts1.filter_policy      = leveldb::NewBloomFilter(10);
      char dbname[1024];
      leveldb::Status stat;

      leveldb::Options opts1;
      opts1.create_if_missing  = true;
      //opts1.compression        = leveldb::kNoCompression;
      //opts1.filter_policy      = leveldb::NewBloomFilter(10);
      sprintf(dbname, "%s/leveldb_rawheaders", baseDir_);
      checkStatus(leveldb::DB::Open(opts1, dbname,  &db_rawheaders_));


      leveldb::Options opts2;
      opts2.create_if_missing  = true;
      //opts2.compression        = leveldb::kNoCompression;
      //opts2.filter_policy      = leveldb::NewBloomFilter(10);
      sprintf(dirname, "%s/leveldb_blockstore", baseDir_);
      checkStatus(leveldb::DB::Open(opts2, dbname,  &db_merklelist_));

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



   bool addBlock



   bool checkStatus(leveldb::Status stat)
   {
      if( stat.ok() )
         return true;
   
      cout << "***LevelDB Error: " << stat.ToString() << endl;
      return false;
   }



private:
   string baseDir_;
   
   leveldb::DB* db_rawheaders_;  // HeaderHash (32B) --> Header Info
   leveldb::DB* db_blockstore_;  // Everything else

};


#endif
