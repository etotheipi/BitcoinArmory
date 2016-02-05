////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "BlockDataMap.h"
#include "BtcUtils.h"

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
   bool preloadFile, bool prefetchNext) :
   path_(path), 
   preloadFile_(preloadFile), prefetchNext_(prefetchNext), prefix_("blk")
{
   //set gcLambda
   gcLambda_ = [this](void)->void
   { this->gcCondVar_.notify_all(); };

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
BlockFileMapPointer&& BlockDataLoader::get(const string& filename)
{
   //convert to int ID
   auto intID = nameToIntID(filename);

   //get with int ID
   return get(intID, prefetchNext_);
}

/////////////////////////////////////////////////////////////////////////////
BlockFileMapPointer&& BlockDataLoader::get(uint32_t fileid, bool prefetch)
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

      //if the prefetch flag is set, get the next file
      if (prefetch)
         get(fileid + 1, false);
   }
   
   //wait then get future
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

   filename << path_ << "blk";
   filename << setw(5) << setfill('0') << fileid;
   filename << ".dat";

   return filename.str();
}

/////////////////////////////////////////////////////////////////////////////
shared_future<shared_ptr<BlockDataFileMap>> 
   BlockDataLoader::getNewBlockDataMap(uint32_t fileid)
{
   auto&& filename = intIDToName(fileid);

   auto blockdataasync = [](string&& filename, bool preload)->
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
   fd = open(filename, O_RDONLY);
#endif
   if (fd == -1)
      return;

   size_ = lseek(fd, 0, SEEK_END);
   lseek(fd, 0, SEEK_SET);

   char* data = nullptr;

#ifdef _WIN32
   //create mmap
   int rc;
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
   fileMap_ = mmap(addr, size_, PROT_READ, 0,
      fd, 0);
   if (fileMap_ == MAP_FAILED) {
      fileMap_ = NULL;
      stringstream errStr;
      errStr << "Failed to create map of file. Error Code: " << errno;
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
