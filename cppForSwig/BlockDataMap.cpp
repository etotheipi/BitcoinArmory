////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataMap.h"
#include "BtcUtils.h"

////////////////////////////////////////////////////////////////////////////////
void BlockData::deserialize(const uint8_t* data, size_t size,
   const BlockHeader* blockHeader, bool checkMerkle)
{
   headerPtr_ = blockHeader;

   //deser header from raw block and run a quick sanity check
   if (size < HEADER_SIZE)
      throw runtime_error("raw data is smaller than HEADER_SIZE");

   BinaryDataRef bdr(data, HEADER_SIZE);
   BlockHeader bh(bdr);

   blockHash_ = bh.thisHash_;

   BinaryRefReader brr(data + HEADER_SIZE, size - HEADER_SIZE);
   auto numTx = (unsigned)brr.get_var_int();

   if (blockHeader != nullptr)
   {
      if (bh.getThisHashRef() != blockHeader->getThisHashRef())
         throw runtime_error("raw data does not match expected block hash");

      if (numTx != blockHeader->getNumTx())
         throw runtime_error("tx count mismatch in deser header");
   }

   for (unsigned i = 0; i < numTx; i++)
   {
      //light tx deserialization, just figure out the offset and size of
      //txins and txouts
      vector<size_t> offsetIns, offsetOuts;
      auto txSize = BtcUtils::TxCalcLength(
         brr.getCurrPtr(), brr.getSizeRemaining(),
         &offsetIns, &offsetOuts);

      //create BCTX object and fill it up
      shared_ptr<BCTX> tx = make_shared<BCTX>(brr.getCurrPtr(), txSize);
      tx->version_ = READ_UINT32_LE(brr.getCurrPtr());

      //first tx in block is always the coinbase
      if (i == 0)
         tx->isCoinbase_ = true;

      //convert offsets to offset + size pairs
      for (int y = 0; y < offsetIns.size() - 1; y++)
         tx->txins_.push_back(
         make_pair(
         offsetIns[y],
         offsetIns[y + 1] - offsetIns[y]));

      for (int y = 0; y < offsetOuts.size() - 1; y++)
         tx->txouts_.push_back(
         make_pair(
         offsetOuts[y],
         offsetOuts[y + 1] - offsetOuts[y]));

      tx->lockTime_ = READ_UINT32_LE(brr.getCurrPtr() + offsetOuts.back());

      //move it to BlockData object vector
      txns_.push_back(move(tx));

      //increment ptr offset
      brr.advance(txSize);
   }

   data_ = data;
   size_ = size;

   if (!checkMerkle)
      return;

   //let's check the merkle root
   vector<BinaryData> allhashes;
   for (auto& txn : txns_)
   {
      BinaryDataRef txdata(txn->data_, txn->size_);
      auto&& txhash = BtcUtils::getHash256(txdata);
      allhashes.push_back(txhash);
   }

   auto&& merkleroot = BtcUtils::calculateMerkleRoot(allhashes);
   if (merkleroot != bh.getMerkleRoot())
      throw BlockDeserializingException("invalid merkle root");
}

/////////////////////////////////////////////////////////////////////////////
BlockHeader BlockData::createBlockHeader(void) const
{
   if (headerPtr_ != nullptr)
      return *headerPtr_;

   BlockHeader bh;

   bh.dataCopy_ = move(BinaryData(data_, HEADER_SIZE));

   bh.difficultyDbl_ = BtcUtils::convertDiffBitsToDouble(
      BinaryDataRef(data_ + 72, 4));

   bh.isInitialized_ = true;
   bh.nextHash_ = BinaryData(0);
   bh.blockHeight_ = UINT32_MAX;
   bh.difficultySum_ = -1;
   bh.isMainBranch_ = false;
   bh.isOrphan_ = true;
   
   bh.numBlockBytes_ = size_;
   bh.numTx_ = txns_.size();

   bh.blkFileNum_ = fileID_;
   bh.blkFileOffset_ = offset_;
   bh.thisHash_ = blockHash_;

   return bh;
}

/////////////////////////////////////////////////////////////////////////////
void BlockFiles::detectAllBlockFiles()
{
   if (folderPath_.size() == 0)
      throw runtime_error("empty block files folder path");

   unsigned numBlkFiles = filePaths_.size();

   while (numBlkFiles < UINT16_MAX)
   {
      string path = BtcUtils::getBlkFilename(folderPath_, numBlkFiles);
      uint64_t filesize = BtcUtils::GetFileSize(path);
      if (filesize == FILE_DOES_NOT_EXIST)
         break;

      filePaths_.insert(make_pair(numBlkFiles, path));

      totalBlockchainBytes_ += filesize;
      numBlkFiles++;
   }
}

/////////////////////////////////////////////////////////////////////////////
BlockDataLoader::BlockDataLoader(const string& path,
   bool preloadFile, bool prefetchNext, bool enableGC) :
   path_(path), 
   preloadFile_(preloadFile), prefetchNext_(prefetchNext), 
   prefix_("blk"), enableGC_(false)
{
   //set gcLambda
   gcLambda_ = [this](void)->void
   { 
      if (!enableGC_)
         return;

	   this->gcCondVar_.notify_all(); 
   };
   
   if (!enableGC_)
      return;

   //start up GC thread
   auto gcthread = [this](void)->void
   { this->garbageCollectorThread(); };

   gcThread_ = thread(gcthread);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataLoader::garbageCollectorThread()
{
   unique_lock<mutex> lock(gcMu_);

   while (run_)
   {
      gcCondVar_.wait(lock);

      //lock the map
      unique_lock<mutex> mapLock(mu_);

      auto mapIter = fileMaps_.begin();
      while (mapIter != fileMaps_.end())
      {
         auto mapFuture = mapIter->second;

         if (!mapFuture.valid())
            continue;

         //emulating a try_lock, we're no interested in futures still waiting
         //on a promise for gc operations
         if (mapFuture.wait_for(std::chrono::milliseconds(1)) 
            != future_status::ready)
            continue;
         
         //TODO: make sure the gc doesn't go after prefetched files right away

         //check the BlockDataMap counter
         auto ptr = mapFuture.get();
         
         int counter = ptr->useCounter_.load(memory_order_relaxed);
         if (counter <= 0)
         {
            counter--;
            ptr->useCounter_.store(counter, memory_order_relaxed);
         }

         if (counter <= -2)
            fileMaps_.erase(mapIter++);
         else
            ++mapIter;
      }
   }
}

/////////////////////////////////////////////////////////////////////////////
BlockFileMapPointer BlockDataLoader::get(const string& filename)
{
   //convert to int ID
   auto intID = nameToIntID(filename);

   //get with int ID
   return get(intID, prefetchNext_);
}

/////////////////////////////////////////////////////////////////////////////
BlockFileMapPointer BlockDataLoader::get(uint32_t fileid, bool prefetch)
{
   //have some fun with promise/future
   shared_future<shared_ptr<BlockDataFileMap>> fMap;

   //lock map, look for fileid entry
   {
      unique_lock<mutex> lock(mu_);

      auto mapIter = fileMaps_.find(fileid);
      if (mapIter == fileMaps_.end())
      {
         //don't have this fileid yet, create it
         fMap = getNewBlockDataMap(fileid);
         fileMaps_[fileid] = fMap;
      }
      else fMap = mapIter->second;
   }

   //if the prefetch flag is set, get the next file
   auto prefetchLambda = [&](unsigned fileID)
      ->BlockFileMapPointer
   { return get(fileID, false); };

   if (prefetch)
   {
      thread tid(prefetchLambda, fileid + 1);
      tid.detach();
   }
   
   fMap.wait();
   return BlockFileMapPointer(fMap.get(), gcLambda_);
}

/////////////////////////////////////////////////////////////////////////////
uint32_t BlockDataLoader::nameToIntID(const string& filename)
{
   if (filename.size() < 3 ||
      strncmp(prefix_.c_str(), filename.c_str(), 3))
      throw runtime_error("invalid filename");

   auto&& substr = filename.substr(3);
   return stoi(substr);
}

/////////////////////////////////////////////////////////////////////////////
string BlockDataLoader::intIDToName(uint32_t fileid)
{
   stringstream filename;

   filename << path_ << "/blk";
   filename << setw(5) << setfill('0') << fileid;
   filename << ".dat";

   return filename.str();
}

/////////////////////////////////////////////////////////////////////////////
shared_future<shared_ptr<BlockDataFileMap>> 
   BlockDataLoader::getNewBlockDataMap(uint32_t fileid)
{
   string filename = move(intIDToName(fileid));

   auto blockdataasync = [](string filename, bool preload)->
      shared_ptr<BlockDataFileMap>
   {
      shared_ptr<BlockDataFileMap> blockptr = make_shared<BlockDataFileMap>(
         filename, preload);

      return blockptr;
   };

   return async(launch::async, blockdataasync, move(filename), preloadFile_);
}

/////////////////////////////////////////////////////////////////////////////
void BlockDataLoader::reset()
{
   unique_lock<mutex> lock(mu_);
   fileMaps_.clear();
}

/////////////////////////////////////////////////////////////////////////////
BlockDataFileMap::BlockDataFileMap(const string& filename, bool preload)
{
   //relaxed memory order for loads and stores, we only care about 
   //atomicity in these operations
   useCounter_.store(0, memory_order_relaxed);

   //check filename exists and open it, otherwise return nullptr fileMap_
   int fd;

#ifdef _WIN32
   fd = _open(filename.c_str(), _O_RDONLY | _O_BINARY);
#else
   fd = open(filename.c_str(), O_RDONLY);
#endif
   if (fd == -1)
      return;

   size_ = lseek(fd, 0, SEEK_END);
   lseek(fd, 0, SEEK_SET);

   char* data = nullptr;

#ifdef _WIN32
   //create mmap
   auto fileHandle = (HANDLE)_get_osfhandle(fd);
   HANDLE mh;

   mh = CreateFileMapping(fileHandle, NULL, PAGE_READONLY,
   0, size_, NULL);
   if (!mh)
   {
      auto errorCode = GetLastError();
      stringstream errStr;
      errStr << "Failed to create map of file. Error Code: " << errorCode;
      throw runtime_error(errStr.str());
   }

   fileMap_ = (uint8_t*)MapViewOfFileEx(mh, FILE_MAP_READ, 0, 0, size_, NULL);
   if (fileMap_ == nullptr)
   {
      auto errorCode = GetLastError();
      stringstream errStr;
      errStr << "Failed to create map of file. Error Code: " << errorCode;
      throw runtime_error(errStr.str());
   }

   CloseHandle(mh);
   //preload as indicated
   if (preload)
   {
      data = new char[size_];
      _read(fd, data, size_);
   }

   _close(fd);
#else
   fileMap_ = (uint8_t*)mmap(0, size_, PROT_READ, MAP_SHARED,
      fd, 0);
   if (fileMap_ == MAP_FAILED) {
      fileMap_ = NULL;
      stringstream errStr;
      errStr << "Failed to create map of file. Error Code: " << errno;
	cout << errStr;
      throw runtime_error(errStr.str());
   }

   //preload as indicated
   if (preload)
   {
      data = new char[size_];
      read(fd, data, size_);
   }

   close(fd);
#endif

   if (data != nullptr)
      delete[] data;
}
