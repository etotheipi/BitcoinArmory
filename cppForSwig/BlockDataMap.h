////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2016, goatpig.                                              //
//  Distributed under the MIT license                                         //
//  See LICENSE-MIT or https://opensource.org/licenses/MIT                    //                                      
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#ifndef _BLOCKDATAMAP_H
#define _BLOCKDATAMAP_H

#include <stdint.h>

#include <mutex>
#include <condition_variable>
#include <thread>
#include <memory>
#include <future>
#include <atomic>

#include <string>
#include <sstream>
#include <iomanip>

#include <map>

using namespace std;

#ifdef _WIN32
#include <Windows.h>
#include <io.h>
#include <fcntl.h>
#else
#include <errno.h>
#endif

/////////////////////////////////////////////////////////////////////////////
class BlockDataFileMap
{
   friend class BlockFileMapPointer;
   friend class BlockDataLoader;

private:
   uint8_t* fileMap_ = nullptr;
   size_t size_ = 0;

   atomic<int> useCounter_;

public:
   BlockDataFileMap(const string& filename, bool preload);

   ~BlockDataFileMap(void)
   {
      //close file mmap
      if (fileMap_ != nullptr)
      {
#ifdef _WIN32
         UnmapViewOfFile(fileMap_);
#else
         munmap(fileMap_, size_);
#endif
         fileMap_ = nullptr;
      }
   }

   const uint8_t* getPtr() const
   {
      return fileMap_;
   }
};

/////////////////////////////////////////////////////////////////////////////
class BlockFileMapPointer
{
private:
   BlockFileMapPointer(const BlockFileMapPointer&) = delete; //no copies

   shared_ptr<BlockDataFileMap> ptr_ = nullptr;
   function<void(void)> gcLambda_;

public:
   BlockFileMapPointer(shared_ptr<BlockDataFileMap> ptr, function<void(void)> gcLambda)
      : ptr_(ptr), gcLambda_(gcLambda)
   {
      //update ptr counter
      ptr_->useCounter_.fetch_add(1, memory_order_relaxed);
   }

   BlockFileMapPointer(BlockFileMapPointer&& mv)
   {
      this->ptr_ = mv.ptr_;
      this->gcLambda_ = move(mv.gcLambda_);
   }
   
   ~BlockFileMapPointer(void)
   {
      if (ptr_ == nullptr)
         return;

      //decrement counter
      ptr_->useCounter_.fetch_sub(1, memory_order_relaxed);

      //notify gcLambda
      gcLambda_();
   }

   shared_ptr<BlockDataFileMap> get(void)
   {
      return ptr_;
   }

   size_t size(void) const
   {
      return ptr_->size_;
   }
};

/////////////////////////////////////////////////////////////////////////////
class BlockDataLoader
{
private:
   map<uint32_t, shared_future<shared_ptr<BlockDataFileMap>>> fileMaps_;
   
   mutex gcMu_, mu_;
   thread gcThread_;
   condition_variable gcCondVar_;
   bool run_ = true;
   
   //preload file in RAM to leverage cache hits on upcoming reads
   const bool preloadFile_  = false; 

   //prefetch next file, expecting the code to read it soon. Will preload 
   //it if the flag is set
   const bool prefetchNext_ = false;

   const string path_;
   const string prefix_;

   function<void(void)> gcLambda_;

private:   

   BlockDataLoader(const BlockDataLoader&) = delete; //no copies

   void garbageCollectorThread(void);
   uint32_t nameToIntID(const string& filename);
   string intIDToName(uint32_t fileid);

   shared_future<shared_ptr<BlockDataFileMap>> getNewBlockDataMap(uint32_t fileid);

public:
   BlockDataLoader(const string& path,
      bool preloadFile, bool prefetchNext);

   ~BlockDataLoader(void)
   {
      //shutdown GC thread
      unique_lock<mutex> lock(gcMu_);
      run_ = false;
      gcCondVar_.notify_all();
      
      if (gcThread_.joinable())
         gcThread_.join();
   }

   BlockFileMapPointer&& get(const string& filename);
   BlockFileMapPointer&& get(uint32_t fileid, bool prefetch);

   void reset(void);
};

#endif