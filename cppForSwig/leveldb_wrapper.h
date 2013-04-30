#ifndef _LEVELDB_WRAPPER_
#define _LEVELDB_WRAPPER_

#include <sstream>
#include "BinaryData.h"
#include "leveldb/db.h"
#include "BlockObj.h"
#include "BtcUtils.h"

#include "leveldb/db.h"
#include "leveldb/write_batch.h"


////////////////////////////////////////////////////////////////////////////////
//
// Create & manage a bunch of different databases
//
//
////////////////////////////////////////////////////////////////////////////////


#define LDB_PREFIX_HEADER   0x00
#define LDB_PREFIX_TXDATA   0x01
#define LDB_PREFIX_SCRIPT   0x02
#define LDB_PREFIX_TRIENODE 0x03
#define LDB_MEMADDR_MAX   (1<<48)

typedef enum
{
  LDB_TX_EXISTS,
  LDB_TX_GETBLOCK,
  LDB_TX_UNKNOWN
} LDB_TX_AVAIL

class InterfaceToLevelDB
{
public:
   InterfaceToLevelDB(string basedir, 
                      BinaryData const & genesisBlkHash,
                      BinaryData const & genesisTxHash,
                      BinaryData const & magic)
   {
      baseDir_ = basedir;
      char dbname[1024];

      stringstream head;
      head << baseDir_ << "/" << "leveldb_headers"
      headPath_ = head.str()

      stringstream blk;
      blk << baseDir_ << "/" << "leveldb_blkdata"
      blkPath_ = blk.str()
      
      magicBytes_ = magic;
      genesisTxHash_ = genesisTxHash
      genesisBlkHash_ = genesisBlkHash;

      // Open databases and check that everything is correct
      // Or create the databases and start it up
      openDatabases();

   }

private:
   BinaryData txOutScriptToLevelDBKey(BinaryData const & script)
   {
      BinaryWriter bw;
      bw.put_uint8_t(LDB_PREFIX_SCRIPT)
      bw.put_var_int(script.getSize()) 
      bw.put_BinaryData(script.getRef());
      return bw.getData();
   }


   /*
   BinaryData memLocToLevelDBKey(uint64_t ldbAddr):
   {
      if(ldbAddr >= LDB_MEMADDR_MAX)
      {
         cout << "***ERROR: LevelDB address out of range: " << ldbAddr << endl;
         return BinaryData(0);
      }

      uint16_t top2 = ldbAddr>>32;
      uint32_t bot4 = ldbAddr & 0xffffffff;

      BinaryWriter bw;
      bw.put_uint8_t(LDB_PREFIX_MEMLOC);
      bw.put_uint16_t(top2);
      bw.put_uint32_t(bot4);
      return bw.getData();
   }
   */

   /////////////////////////////////////////////////////////////////////////////
   BinaryData headerHashToLevelDBKey(BinaryData const & headHash)
   {
      BinaryWriter bw;
      bw.put_uint8_t(LDB_PREFIX_HEADER);
      bw.put_BinaryData(headHash);
      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   BinaryData txHashToLevelDBKey(BinaryData const & txHash)
   {
      // We actually only store the first four bytes of the tx
      BinaryWriter bw;
      bw.put_uint8_t(LDB_PREFIX_TXDATA);
      bw.put_BinaryData(txHash, 0, 4);
      return bw.getData();
   }

   /////////////////////////////////////////////////////////////////////////////
   void openDatabases(void)
   {
      if(genesisBlkHash_.getSize() == 0 || magicBytes_.getSize() == 0)
      {
         cerr << "***ERROR:  must set magic bytes and genesis block!" << endl;
         return;
      }

      //opts1.filter_policy      = leveldb::NewBloomFilter(10);
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

      BinaryData key(string("DatabaseInfo"))
      BinaryData headDBInfo = getValue(db_headers_, key);
      if(headDBInfo.getSize() == 0)
      {
         // If this database is new, create the "DatabaseInfo" key
         BinaryWriter bw;
         bw.put_BinaryData(magicBytes_);
         bw.put_uint32_t(0);
         bw.put_BinaryData(genesisBlkHash_);
         putValue(db_headers_, key, bw.getData());
      }
      else
      {
         // Else we read the DB info and make sure everything matches up
         if(headDBInfo.getSize() < 40)
         {
            cerr << "***ERROR: Invalid DatabaseInfo data" << endl;
            closeDatabases();
            return;
         }
         BinaryReader br(headDBInfo);
         BinaryData magic = br.get_BinaryData(4);
         topBlockHeight_  = br.get_uint32_t(4);
         topBlockHash_    = br.get_BinaryData(32);
      
         // Check that the magic bytes are correct
         if(magicBytes_ != magic)
         {
            cerr << "***ERROR:  Magic bytes mismatch!  Different blkchain?" << endl;
            closeDatabases();
            return;
         }
         
         // Check that we have the top hash (not sure about if we don't)
         if( getValue(db_headers_, topBlockHash_).getSize() == 0 )
         {
            cerr << "***ERROR:  Top block doesn't exist!" << endl;
            closeDatabases();
            return;
         }
         
      }

   }




   
   /////////////////////////////////////////////////////////////////////////////
   // DBs don't really need to be closed.  
   void closeDatabases(void)
   {
      delete db_headers_;
      delete db_blkdata_;
   }


   /////////////////////////////////////////////////////////////////////////////
   // Get value using pre-created slice
   BinaryData getValue(leveldb::DB* db, leveldb::Slice ldbKey)
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
   BinaryData getValue(leveldb::DB* db, BinaryData const & key)
   {
      string value;
      leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
      
      leveldb::Status stat = db->Get(leveldb::ReadOptions(), ldbkey, &value);
      if(stat==Status::IsNotFound())
         return BinaryData(0);

      checkStatus(stat);
      return BinaryData(value);
   }


   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void putValue(leveldb::DB* db, 
                 BinaryData const & key, 
                 BinaryData const & value,
                 leveldb::WriteBatch* batch=NULL)
   {
      leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
      leveldb::Slice ldbVal((char*)value.getPtr(), value.getSize());
      
      if(batch==NULL)
      {
         leveldb::Status stat = db->Put(leveldb::ReadOptions(), ldbkey, &value);
         checkStatus(stat);
      }
      else
         batch->Put(ldbkey, &value);
   }


   /////////////////////////////////////////////////////////////////////////////
   // Put value based on BinaryData key.  If batch writing, pass in the batch
   void deleteValue(leveldb::DB* db, BinaryData const & key, 
                       leveldb::WriteBatch* batch=NULL)
   {
      string value;
      leveldb::Slice ldbKey((char*)key.getPtr(), key.getSize());
      
      if(batch==NULL)
      {
         leveldb::Status stat = db->Put(leveldb::ReadOptions(), ldbkey, &value);
         checkStatus(stat);
      }
      else
         batch->Put(ldbkey, &value);
   }

   BinaryData sliceToBinaryData(leveldb::Slice slice)
   {
      return BinaryData((uint8_t*)(slice.data()), slice.size())
   }

   void sliceToBinaryData(leveldb::Slice slice, BinaryData & bd)
   {
      bd.copyFrom((uint8_t*)(slice.data()), slice.size())
   }

   /////////////////////////////////////////////////////////////////////////////
   void startHeaderIteration(void)
   {
      iterHeaders_ = db_headers_->NewIterator(leveldb::ReadOptions());
      iterHeaders_->SeekToFirst();

      // Skip the first entry which is the DatabaseInfo key
      if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey )
         cerr << "***WARNING: How do we not have a DB info key?" << endl; 
      else
         iterHeaders_->Next()
   }

   /////////////////////////////////////////////////////////////////////////////
   void startBlockIteration(void)
   {
      iterBlkData_ = db_blkdata_->NewIterator(leveldb::ReadOptions());
      iterBlkData_->SeekToFirst();

      // Skip the first entry which is the DatabaseInfo key
      if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey )
         cerr << "***WARNING: How do we not have a DB info key?" << endl; 
      else
         iterBlkData_->Next()
   }

   /////////////////////////////////////////////////////////////////////////////
   map<HashString, BlockHeader> getHeaderMap(void)
   {
      map<HashString, BlockHeader> outMap;

      leveldb::Iterator* it = db_headers_->NewIterator(leveldb::ReadOptions());
      it->SeekToFirst();
      if( sliceToBinaryData(ldbiter->key()) != getDBInfoKey )
         cerr << "***WARNING: How do we not have a DB info key?" << endl; 
      else:
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
         header.setStoredHeight(hgtX >> 8);
         header.setDuplicateID(hgtX | 0x000000ff);

         outMap[headerHash] = header;
      }

      return outMap;
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
                 //db_headers_.NewIterator(leveldb::ReadOptions());

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
      stat = db_headers_.Get(leveldb::ReadOptions(), key, &headerVal);
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
      
      stat = db_headers_.Put(leveldb::WriteOptions(), key, val);
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

   BinaryData getDBInfoKey(void)
   {
      // Make the 20-bytes of zeros followed by "DatabaseInfo".  We
      // do this to make sure it's always at the beginning of an iterator
      // loop and we can just skip the first entry, instead of checking
      // each key in the loop
      static BinaryData dbinfokey(0);
      if(dbinfokey.getSize() == 0)
      {
         BinaryWriter bw;
         bw.put_uint64_t(0)
         bw.put_uint64_t(0)
         bw.put_uint32_t(0)
         bw.put_BinaryData( BinaryData(string("DatabaseInfo")));
         dbinfokey = bw.getData();
      }
      return dbinfokey;
   }



private:
   string baseDir_;
   string headPath_;
   string blkPath_;

   BinaryData genesisBlkHash_;
   BinaryData genesisTxHash_;
   BinaryData magicBytes_;

   HashString topBlockHash_;
   uint32_t   topBlockHeight_;

   leveldb::Iterator* iterHeaders_;
   leveldb::Iterator* iterBlkData_;
   
   leveldb::DB* db_headers_;  // HeaderHash (32B) --> Header Info
   leveldb::DB* db_blkdata_;  // Everything else

};


#endif
